"""Compatibility shim: gallery refreshes now write only ignored catalog.js."""
from reel.catalog import build_catalog


def build_gallery_html():
    return build_catalog()


if __name__ == "__main__":
    print(build_catalog())

