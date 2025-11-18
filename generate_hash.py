import sys

try:
    import streamlit_authenticator as stauth  # may not always have .Hasher.generate()
except ImportError:
    stauth = None

passwords = ["team#5", "sharp#123", "rockwell#456", "parmesan#789"]

hashes = None
if stauth is not None:
    try:
        # Common API
        hashes = stauth.Hasher(passwords).generate()
    except Exception:
        try:
            # Some versions expose .hash()
            hashes = stauth.Hasher(passwords).hash()
        except Exception:
            try:
                # Older API: constructor without args + generate(list)
                hasher = stauth.Hasher()
                hashes = hasher.generate(passwords)
            except Exception:
                try:
                    # Older API: constructor without args + hash(list)
                    hasher = stauth.Hasher()
                    hashes = hasher.hash(passwords)
                except Exception:
                    hashes = None

if hashes is None:
    # Fallback: bcrypt directly
    import bcrypt
    print("Using bcrypt fallback (streamlit-authenticator Hasher API not available).")
    hashes = [bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8") for p in passwords]

print(hashes)