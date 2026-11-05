import urllib.request
import json
import ssl
import uuid
from apply_rules_and_test_pages import load_env, notion_request

env = load_env()
token = env['NOTION_TOKEN']
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# 1x1 minimal transparent PNG
png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7V\x01\x84\x00\x00\x00\x00IEND\xaeB`\x82'

print("1. Creating file upload object...")
res = notion_request('POST', 'file_uploads', token, {
    'mode': 'single_part',
    'filename': 'test_dot.png',
    'content_type': 'image/png'
})
f_id = res['id']
upload_url = res['upload_url']
print('Upload initialized:', f_id)

print("2. Sending multipart data with file field...")
boundary = uuid.uuid4().hex
crlf = b"\r\n"
multipart_data = (
    f"--{boundary}\r\n".encode() +
    b'Content-Disposition: form-data; name="file"; filename="test_dot.png"\r\n' +
    b'Content-Type: image/png\r\n\r\n' +
    png_bytes +
    b"\r\n" +
    f"--{boundary}--\r\n".encode()
)

req = urllib.request.Request(
    upload_url,
    data=multipart_data,
    headers={
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req, context=SSL_CTX) as resp:
        print('Binary upload response code:', resp.status)
        body = resp.read().decode('utf-8', errors='ignore')
        print('Binary upload body:', body)
except urllib.error.HTTPError as e:
    print('HTTP Error code:', e.code)
    print('HTTP Error body:', e.read().decode('utf-8', errors='ignore'))
    exit(1)

print("3. Attaching block to page...")
pid = '4003818f-8ba0-80cf-bf95-ef15001d8a52'
attach_payload = {
    'children': [
        {
            'object': 'block',
            'type': 'image',
            'image': {
                'type': 'file_upload',
                'file_upload': {'id': f_id}
            }
        }
    ]
}
attach_res = notion_request('PATCH', f'blocks/{pid}/children', token, attach_payload)
added_id = attach_res['results'][0]['id']
print('Successfully attached file_upload image block!', added_id)

notion_request('DELETE', f'blocks/{added_id}', token)
print('Cleaned up test block successfully!')
