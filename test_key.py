import os
from google import genai

# Thay chuỗi key thực tế của bạn vào đây để test trực tiếp
client = genai.Client(api_key="AIzaSyB4yPJzCODyVUOld2zNWdIMSEvguURzZvE") 

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Hi',
    )
    print("Thành công! Phản hồi từ Gemini:", response.text)
except Exception as e:
    print("Lỗi từ Google:", str(e))