from mcp.server.fastmcp import FastMCP
from PIL import Image
import pytesseract

mcp = FastMCP("ocr-generic")

@mcp.tool()
def ocr_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        txt = pytesseract.image_to_string(img)
        return txt
    except Exception:
        return ""

if __name__ == "__main__":
    mcp.run()
