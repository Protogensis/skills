#!/usr/bin/env python3
"""Grok 生图通道：通过同一中转站(base_url) + GROK_API_KEY 调用 grok 生图模型。

用法:
  grok_gen.py generate --prompt "..." [--size 1024x1024] [--quality low|medium|high] [--out out.png] [--model 模型名]
  grok_gen.py edit --image 原图.png --prompt "修改指令" [--out out.png] [--model 模型名]

环境变量(从 .env 或 export 读取):
  OPENAI_BASE_URL  中转站地址(与 openai key 共用)
  GROK_API_KEY     grok key
  GROK_IMAGE_MODEL 默认 grok-imagine-image-quality(中转站可能有别的名字)
"""
import argparse, base64, os, sys

def client():
    from openai import OpenAI
    base = os.environ.get("OPENAI_BASE_URL")
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

def cmd_generate(a):
    c = client()
    try:
        resp = c.images.generate(
            model=a.model, prompt=a.prompt,
            n=1, size=a.size,
            quality=a.quality if a.quality else "auto",
            response_format="b64_json",
        )
    except Exception:
        # 中转站/模型不支持 response_format 参数时退回默认(url)
        resp = c.images.generate(
            model=a.model, prompt=a.prompt,
            n=1, size=a.size,
            quality=a.quality if a.quality else "auto",
        )
    save(resp, a.out)

def cmd_edit(a):
    c = client()
    with open(a.image, "rb") as f:
        img = f.read()
    resp = c.images.edit(
        model=a.model, image=img,
        prompt=a.prompt, n=1, size=a.size,
    )
    save(resp, a.out)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--prompt", required=True)
    g.add_argument("--size", default="1024x1024")
    g.add_argument("--quality")
    g.add_argument("--out", required=True)
    g.add_argument("--model", default=os.environ.get("GROK_IMAGE_MODEL", "grok-imagine-image-quality"))
    g.set_defaults(fn=cmd_generate)
    e = sub.add_parser("edit")
    e.add_argument("--image", required=True)
    e.add_argument("--prompt", required=True)
    e.add_argument("--size", default="1024x1024")
    e.add_argument("--out", required=True)
    e.add_argument("--model", default=os.environ.get("GROK_EDIT_MODEL", "grok-imagine-edit"))
    e.set_defaults(fn=cmd_edit)
    a = ap.parse_args()
    a.fn(a)

if __name__ == "__main__":
    main()
