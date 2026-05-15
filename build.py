import os
import shutil
import sys
import subprocess
from datetime import datetime

# 请在项目根目录执行: python build.py（或运行 build.bat）

ROOT = os.path.dirname(os.path.abspath(__file__))


def _prepare_icon_square_master(img):
    """去掉画布黑边/字母边，再居中裁成正方形，避免 ICO 里左右留黑、图形被压扁。"""
    from PIL import Image, ImageChops

    img = img.convert("RGBA")
    r, g, b, _a = img.split()
    m1 = ImageChops.lighter(r, g)
    mx = ImageChops.lighter(m1, b)
    # 任一通道高于阈值即视为「画面内容」，用于裁掉四周纯黑画布
    mask = mx.point(lambda p: 255 if p > 18 else 0)
    bbox = mask.getbbox()
    if bbox is not None:
        x0, y0, x1, y1 = bbox
        pad = max(3, int(0.025 * max(x1 - x0, y1 - y0)))
        w, h = img.size
        x0 = max(0, x0 - pad)
        y0 = max(0, y0 - pad)
        x1 = min(w, x1 + pad)
        y1 = min(h, y1 + pad)
        if x1 - x0 > 24 and y1 - y0 > 24:
            img = img.crop((x0, y0, x1, y1))
    w, h = img.size
    if w != h:
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
    return img


def _resize_cover_square(img, side: int):
    """等比缩放以完全覆盖 side×side，再居中裁剪；母图非方时也不会被硬拉变形。"""
    from PIL import Image

    w, h = img.size
    if w <= 0 or h <= 0:
        return img.resize((side, side), Image.Resampling.LANCZOS)
    scale = max(side / w, side / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - side) // 2
    top = (nh - side) // 2
    return resized.crop((left, top, left + side, top + side))


def _knockout_edge_nearblack(img, band_px: int, lum_max: int = 52):
    """仅处理贴边窄带内的近黑像素，去掉歪黑边，不伤中间霓虹深色底。"""
    w, h = img.size
    band_px = max(2, min(band_px, w // 3, h // 3))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if min(x, y, w - 1 - x, h - 1 - y) > band_px:
                continue
            r, g, b, a = px[x, y]
            if max(r, g, b) < lum_max:
                px[x, y] = (0, 0, 0, 0)
    return img


def _apply_squircle_alpha(
    img,
    inset_ratio: float = 0.012,
    corner_radius_ratio: float = 0.235,
):
    """圆角矩形（squircle 观感）外全透明：四角画布黑底去掉，霓虹圆角框保留。

    与全透明底合成，减轻半透明边缘叠在黑底上发灰。
    """
    from PIL import Image, ImageChops, ImageDraw, ImageFilter

    w, h = img.size
    m = max(0.0, min(w, h) * inset_ratio)
    x0, y0 = int(m), int(m)
    x1, y1 = w - int(m), h - int(m)
    side = max(1, min(x1 - x0, y1 - y0))
    rx = int(round(side * corner_radius_ratio))
    rx = max(0, min(rx, side // 2))

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=rx, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.42))
    r, g, b, a = img.split()
    a2 = ImageChops.multiply(a, mask)
    out = Image.merge("RGBA", (r, g, b, a2))
    transparent = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return Image.composite(out, transparent, a2)


def _ensure_clickdone_ico() -> None:
    """从 D 稿 PNG 生成多尺寸 clickdone.ico，供 PyInstaller --icon 使用。

    裁方 → 贴边抠黑 → 圆角矩形外透明 → 锐化 → 各档缩放（每档再套同形蒙版）→ PNG 帧 ICO。
    """
    png = os.path.join(ROOT, "design", "branding", "clickdone-icon-concept-D.png")
    ico = os.path.join(ROOT, "design", "branding", "clickdone.ico")
    if not os.path.isfile(png):
        print("Warning: design/branding/clickdone-icon-concept-D.png missing, skip .ico")
        return
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        print("Warning: Pillow not installed; pip install Pillow to auto-generate clickdone.ico")
        return

    img = Image.open(png).convert("RGBA")
    img = _prepare_icon_square_master(img)
    side = min(img.size)
    img = _knockout_edge_nearblack(img, max(14, int(0.065 * side)))
    img = _apply_squircle_alpha(img, inset_ratio=0.012, corner_radius_ratio=0.235)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=65, threshold=2))

    sizes = (256, 128, 96, 72, 64, 48, 40, 32, 24, 20, 16)
    imgs = []
    for s in sizes:
        r = _resize_cover_square(img, s)
        r = _apply_squircle_alpha(r, inset_ratio=0.012, corner_radius_ratio=0.235)
        r = _knockout_edge_nearblack(r, max(2, int(0.08 * s)), lum_max=55)
        if s <= 48:
            r = r.filter(ImageFilter.UnsharpMask(radius=0.5, percent=125, threshold=1))
        imgs.append(r)

    save_kw = dict(
        format="ICO",
        sizes=[(im.width, im.height) for im in imgs],
        append_images=imgs[1:],
    )
    save_kw["bitmap_format"] = "png"

    imgs[0].save(ico, **save_kw)
    print(f"Generated {ico}")


def main():
    today = datetime.now()
    date_str = today.strftime("%m%d_%H%M%S")
    date_dir = today.strftime("%Y%m%d")
    output_name = f"ClickDone_{date_str}"

    release_dir = os.path.join(ROOT, "release", date_dir)
    os.makedirs(release_dir, exist_ok=True)

    build_dir = os.path.join(ROOT, "build")
    os.makedirs(build_dir, exist_ok=True)

    print(f"Packaging {output_name}.exe...")
    print(f"Output directory: {release_dir}")

    _ensure_clickdone_ico()

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=ClickDone",
        "--add-data=src/web;web",
        "--add-data=src/config;config",
    ]
    ico_path = os.path.join(ROOT, "design", "branding", "clickdone.ico")
    if os.path.isfile(ico_path):
        args.append("--add-data=design/branding/clickdone.ico;design/branding")
        args.append("--icon=" + ico_path)
    args.extend(
        [
        "--workpath=" + build_dir,
        "--distpath=" + release_dir,
        "--noconfirm",
        os.path.join(ROOT, "src", "main.py"),
        ]
    )

    try:
        result = subprocess.run(
            args, check=False, capture_output=True, text=True, cwd=ROOT
        )

        built_exe = os.path.join(release_dir, "ClickDone.exe")
        output_exe = os.path.join(release_dir, f"{output_name}.exe")

        if os.path.isfile(built_exe):
            os.rename(built_exe, output_exe)
            print(f"Done! Output file: {output_exe}")
            release_config = os.path.join(release_dir, "config")
            os.makedirs(release_config, exist_ok=True)
            defaults_dir = os.path.join(ROOT, "src", "config", "defaults")
            for fn in ("apps.json", "ui.json"):
                src_f = os.path.join(defaults_dir, fn)
                dst_f = os.path.join(release_config, fn)
                if os.path.isfile(src_f) and not os.path.isfile(dst_f):
                    shutil.copy2(src_f, dst_f)
                    print(f"Placed default config: {dst_f}")
        else:
            print(f"Error: ClickDone.exe not found at {built_exe}")
            sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
