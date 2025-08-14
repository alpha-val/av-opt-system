import re, hashlib
def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")
def stable_id(namespace: str, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{slugify(namespace)}_{h}"
