from flask import Flask, request, jsonify
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from reqClan_pb2 import MyMessage

app = Flask(__name__)

# Configuration
KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
IV = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

# URLs - Updated with your JWT endpoint
JWT_URL = "https://duranto-200-100.vercel.app/token"
CLAN_URL = "https://clientbp.ggblueshark.com/RequestJoinClan"

class ClanJoinRequest:
    """Handle single clan join request"""
    
    def __init__(self, uid, password, clan_id):
        self.uid = uid
        self.password = password
        self.clan_id = clan_id
        self.session = requests.Session()
    
    def get_jwt_token(self):
        """Get JWT token for the account from your API"""
        try:
            response = requests.get(
                f"{JWT_URL}?uid={self.uid}&password={self.password}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'live' and 'token' in data:
                    return data['token']
                else:
                    print(f"❌ JWT API returned error: {data}")
            else:
                print(f"❌ JWT API status code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ JWT error for {self.uid}: {e}")
        return None
    
    def create_encrypted_payload(self):
        """Create encrypted payload for clan join request"""
        try:
            message = MyMessage()
            message.field_1 = int(self.clan_id)
            serialized_data = message.SerializeToString()
            
            cipher = AES.new(KEY, AES.MODE_CBC, IV)
            encrypted_data = cipher.encrypt(pad(serialized_data, AES.block_size))
            return encrypted_data
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return None
    
    def send_join_request(self, jwt_token):
        """Send clan join request"""
        try:
            encrypted_data = self.create_encrypted_payload()
            if not encrypted_data:
                return False
            
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 10; m3 note Build/QD4A.200805.003)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/octet-stream",
                'Authorization': f"Bearer {jwt_token}",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB51",
            }
            
            response = self.session.post(
                CLAN_URL, 
                data=encrypted_data, 
                headers=headers,
                timeout=5
            )
            
            print(f"🔍 Clan join response status: {response.status_code}")
            if response.status_code != 200:
                print(f"🔍 Response text: {response.text}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Request error for {self.uid}: {e}")
            return False
    
    def process_request(self):
        """Process single clan join request"""
        print(f"🚀 Processing clan join for UID: {self.uid}, Clan: {self.clan_id}")
        
        # Get JWT token
        jwt_token = self.get_jwt_token()
        if not jwt_token:
            return {
                'status': 'error',
                'message': 'Failed to get JWT token from API',
                'uid': self.uid
            }
        
        print(f"✅ JWT token obtained: {jwt_token[:50]}...")
        
        # Send join request
        success = self.send_join_request(jwt_token)
        
        if success:
            return {
                'status': 'success',
                'message': 'Clan join request sent successfully',
                'uid': self.uid,
                'clan_id': self.clan_id
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to send clan join request to game server',
                'uid': self.uid,
                'clan_id': self.clan_id
            }

@app.route('/join_clan', methods=['GET'])
def join_clan():
    """Single clan join request endpoint"""
    try:
        # Get parameters
        uid = request.args.get('uid')
        password = request.args.get('password')
        clan_id = request.args.get('clan_id')
        
        # Validate parameters
        if not uid:
            return jsonify({
                'status': 'error',
                'message': 'Missing uid parameter'
            }), 400
        
        if not password:
            return jsonify({
                'status': 'error',
                'message': 'Missing password parameter'
            }), 400
            
        if not clan_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing clan_id parameter'
            }), 400
        
        # Create request handler
        clan_join = ClanJoinRequest(uid, password, clan_id)
        
        # Process request
        result = clan_join.process_request()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Clan Join API Server Starting...")
    
    app.run(host='0.0.0.0', port=5000, debug=False)