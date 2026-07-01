# api_client.py
import httpx, base64, cv2

class CampusAI:
    def __init__(self, api_key, base_url):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.base_url = base_url

    async def verify_object(self, frame, label_zh, position, dist):
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        prompt = f"前方{dist}公尺有{label_zh}。請判斷燈號顏色，並給出『可以通行』或『請等待』的指令。限10字以內。"
        
        payload = {
            "model": "vibe",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
            ]}]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=self.headers, timeout=5.0)
                return response.json()['choices'][0]['message']['content'].strip()
            except: 
                return f"前方有{label_zh}，請注意。"