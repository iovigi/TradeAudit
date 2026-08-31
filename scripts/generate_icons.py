"""
Utility script to generate TradeAudit application icons and resources.
"""

from pathlib import Path
from PIL import Image, ImageDraw

def create_tradeaudit_icon(size: int = 512) -> Image.Image:
    """Create a high-resolution crisp application icon."""
    # RGBA image with transparent background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size * 0.06
    # Outer rounded background / dark shield background
    bg_color = (20, 24, 33, 255) # Dark slate
    border_color = (0, 208, 132, 255) # Emerald / Cyan accent
    
    # Draw rounded rectangle background
    corner_radius = size * 0.22
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=corner_radius,
        fill=bg_color,
        outline=border_color,
        width=int(size * 0.03)
    )

    # Draw stylized Candlesticks / Risk-Reward Bars & Shield
    # Candlestick 1 (Bullish green)
    c1_x = size * 0.30
    c1_w = size * 0.10
    # Wick
    draw.line([(c1_x + c1_w/2, size * 0.28), (c1_x + c1_w/2, size * 0.72)], fill=(0, 208, 132, 255), width=int(size * 0.02))
    # Body
    draw.rounded_rectangle([(c1_x, size * 0.38), (c1_x + c1_w, size * 0.62)], radius=int(size*0.015), fill=(0, 208, 132, 255))

    # Candlestick 2 (Central Tall / Gold / Target)
    c2_x = size * 0.46
    c2_w = size * 0.10
    # Wick
    draw.line([(c2_x + c2_w/2, size * 0.20), (c2_x + c2_w/2, size * 0.78)], fill=(255, 184, 0, 255), width=int(size * 0.02))
    # Body
    draw.rounded_rectangle([(c2_x, size * 0.30), (c2_x + c2_w, size * 0.55)], radius=int(size*0.015), fill=(255, 184, 0, 255))

    # Candlestick 3 (Right Bar / Cyan)
    c3_x = size * 0.62
    c3_w = size * 0.10
    # Wick
    draw.line([(c3_x + c3_w/2, size * 0.25), (c3_x + c3_w/2, size * 0.68)], fill=(0, 168, 255, 255), width=int(size * 0.02))
    # Body
    draw.rounded_rectangle([(c3_x, size * 0.35), (c3_x + c3_w, size * 0.58)], radius=int(size*0.015), fill=(0, 168, 255, 255))

    # Draw bottom audit checkmark / target arc
    arc_box = [(size * 0.25, size * 0.68), (size * 0.75, size * 0.82)]
    draw.arc(arc_box, start=0, end=180, fill=(0, 208, 132, 255), width=int(size * 0.025))

    return img


def generate_icon_assets():
    icons_dir = Path(__file__).resolve().parent.parent / "resources" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    master_icon = create_tradeaudit_icon(512)
    
    # Save PNG
    png_path = icons_dir / "tradeaudit.png"
    master_icon.save(png_path, format="PNG")
    print(f"Saved {png_path}")

    # Save Multi-size ICO
    ico_path = icons_dir / "tradeaudit.ico"
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    master_icon.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved {ico_path}")


if __name__ == "__main__":
    generate_icon_assets()
