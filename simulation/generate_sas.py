import sys
import time
import hmac
import hashlib
import base64
import urllib.parse

def generate_sas_token(uri, key, policy_name=None, expiry=3600):
    ttl = time.time() + expiry
    sign_key = "%s\n%d" % ((urllib.parse.quote_plus(uri)), int(ttl))
    signature = base64.b64encode(hmac.new(base64.b64decode(key), msg=sign_key.encode('utf-8'), digestmod=hashlib.sha256).digest())

    rawtoken = {
        'sr' :  uri,
        'sig': signature,
        'se' : str(int(ttl))
    }

    if policy_name is not None:
        rawtoken['skn'] = policy_name

    return 'SharedAccessSignature ' + urllib.parse.urlencode(rawtoken)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 generate_sas.py <hub_host> <device_id> <key>")
        sys.exit(1)
    
    hub = sys.argv[1]
    device = sys.argv[2]
    key = sys.argv[3]
    
    uri = f"{hub}/devices/{device}"
    token = generate_sas_token(uri, key, expiry=31536000) # 1 year expiry
    print(token)
