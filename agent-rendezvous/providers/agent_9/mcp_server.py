from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ocr-generic")

@mcp.tool()
def ocr_image(image_path: str) -> str:
    """Generic OCR for images."""
    return "Generic OCR Text Result"

if __name__ == "__main__":
    mcp.run()
