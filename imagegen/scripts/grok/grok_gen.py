#!/usr/bin/env python3
"""Grok 生图通道：通过 GROK_BASE_URL + GROK_API_KEY 调用 grok 生图模型（与 openai 通道配置互相独立）。

用法:
  grok_gen.py generate --prompt "..." [--aspect-ratio 16:9] [--quality low|medium|high] [--out out.png] [--model 模型名]
  grok_gen.py edit --image 原图.png --prompt "修改指令" [--out out.png] [--model 模型名]

环境变量(从 .env 或 export 读取):
  GROK_BASE_URL     中转站地址（grok 专用；须以 /v1 结尾）
  GROK_API_KEY      grok key
  GROK_IMAGE_MODEL  默认 grok-imagine-image-quality(中转站可能有别的名字)
"""
import argparse, base64, os, re, sys

def client():
    from openai import OpenAI
    base = os.environ.get("GROK_BASE_URL")
    if not base:
        sys.exit("错误: GROK_BASE_URL 未设置（grok 通道独立配置，不读 OPENAI_BASE_URL）")
    key = os.environ.get("GROK_API_KEY")
    if not key:
        sys.exit("错误: GROK_API_KEY 未设置")
    return OpenAI(base_url=base, api_key=key)

def save(resp, out):
    data = resp.data[0]
    b64 = getattr(data, "b64_json", None)
    if b64:
        with open(out, "wb") as f:
            f.write(base64.b64decode(b64))
    else:
        url = data.url
        print(f"图片URL: {url}", file=sys.stderr)
        import urllib.request
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as r, open(out, "wb") as f:
                f.write(r.read())
        except Exception as e:
            sys.exit(f"下载失败: {e}\n可手动重试: curl -A 'Mozilla/5.0' -o {out} '{url}'")
    print(f"已保存: {out}")

ASPECT_RE = r"(?:auto|\d+(?:\.\d+)?:\d+(?:\.\d+)?)"

def cmd_generate(a):
    if not re.fullmatch(ASPECT_RE, a.aspect_ratio):
        sys.exit(f"错误: --aspect-ratio 应为 W:H（如 16:9）或 auto，收到: {a.aspect_ratio}")
    c = client()
    # grok-imagine 系按宽高比出图（官方 Imagine 接口语义），经 extra_body 透传；中转站支持透传
    # quality 仅在用户显式指定时发送：上游拒绝 "auto"（实测 422）
    kwargs = dict(model=a.model, prompt=a.prompt, n=1,
                  extra_body={"aspect_ratio": a.aspect_ratio})
    if a.quality:
        kwargs["quality"] = a.quality
    try:
        resp = c.images.generate(response_format="b64_json", **kwargs)
    except Exception:
        # 中转站/模型不支持 response_format 参数时退回默认(url)
        resp = c.images.generate(**kwargs)
    save(resp, a.out)

def cmd_edit(a):
    c = client()
    with open(a.image, "rb") as f:
        img = f.read()
    # 单图编辑跟随输入图比例（官方 Imagine 语义），不发 size/aspect_ratio
    resp = c.images.edit(
        model=a.model, image=img,
        prompt=a.prompt, n=1,
    )
    save(resp, a.out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--prompt", required=True)
    g.add_argument("--quality", choices=["low", "medium", "high"],
                   help="显式指定时才发送；上游拒绝其他值（auto 实测 422）")
    g.add_argument("--aspect-ratio", dest="aspect_ratio", default="auto",
                   help="宽高比，W:H（如 16:9）或 auto（默认，模型自定）")
    g.add_argument("--out", required=True)
    g.add_argument("--model", default=os.environ.get("GROK_IMAGE_MODEL", "grok-imagine-image-quality"))
    g.set_defaults(fn=cmd_generate)
    e = sub.add_parser("edit")
    e.add_argument("--image", required=True)
    e.add_argument("--prompt", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--model", default=os.environ.get("GROK_EDIT_MODEL", "grok-imagine-edit"))
    e.set_defaults(fn=cmd_edit)
    a = ap.parse_args()
    a.fn(a)

if __name__ == "__main__":
    main()
