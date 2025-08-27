import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import json
from typing import Optional, Dict, Any
import os

# Cấu hình trang
st.set_page_config(
    page_title="🎯 Tạo Ảnh Thẻ AI", 
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main > div {
        padding: 2rem 1rem;
    }
    
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
    }
    
    .upload-section {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #e8f5e8;
        border: 1px solid #4CAF50;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #ffebee;
        border: 1px solid #f44336;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #e3f2fd;
        border: 1px solid #2196F3;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Cấu hình API
API_CONFIG = {
    'endpoint': 'https://api.llm.ai.vn/v1',
    'model': 'gemini:gemini-2.5-flash',
    'api_key': 'sk-j4DkzI7htsVqEZqC272d3b58B0Fb49A183573dD2Fc04F71d'  # Thay thế bằng API key thực
}

class IDPhotoGenerator:
    """Class chính để tạo ảnh thẻ AI"""
    
    def __init__(self):
        self.allowed_formats = ['jpg', 'jpeg', 'png', 'webp', 'bmp']
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        
    def validate_image(self, uploaded_file) -> Dict[str, Any]:
        """Validate file ảnh upload"""
        if not uploaded_file:
            return {'valid': False, 'error': 'Vui lòng tải lên ảnh!'}
            
        # Kiểm tra định dạng
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in self.allowed_formats:
            return {
                'valid': False, 
                'error': f'Định dạng không hỗ trợ! Chỉ chấp nhận: {", ".join(self.allowed_formats)}'
            }
        
        # Kiểm tra kích thước
        if uploaded_file.size > self.max_file_size:
            return {
                'valid': False, 
                'error': f'File quá lớn! Tối đa {self.max_file_size / (1024*1024):.0f}MB'
            }
            
        try:
            # Kiểm tra có phải ảnh hợp lệ không
            image = Image.open(uploaded_file)
            image.verify()
            return {'valid': True, 'image': image}
        except Exception as e:
            return {'valid': False, 'error': f'File ảnh không hợp lệ: {str(e)}'}
    
    def create_prompt(self, gender: str, options: Dict[str, str]) -> str:
        """Tạo prompt cho AI dựa trên options"""
        photo_size = options.get('photo_size', '4x6')
        prompt = f"Create a professional ID photo with {photo_size} dimensions, 300 DPI resolution. "
        
        if gender == 'male':
            suit_style = options.get('suit_style', 'classic')
            suit_color = options.get('suit_color', 'navy')
            tie_style = options.get('tie_style', 'solid')
            
            prompt += f"Male subject wearing a {suit_style} {suit_color} business suit with a {tie_style} necktie. "
            prompt += "Professional formal attire, clean white background. "
            prompt += "IMPORTANT: Keep the original facial features exactly the same, only enhance appearance. "
            
        else:  # female
            outfit = options.get('female_outfit', 'blazer')
            color = options.get('female_color', 'white')
            background = options.get('background', 'white')
            
            prompt += f"Female subject wearing a {color} {outfit}. "
            prompt += f"Professional business attire with {background} background. "
            
        prompt += "Professional portrait photography, soft lighting, high resolution, passport photo quality."
        return prompt
    
    def call_ai_api(self, prompt: str, image_data: str) -> Dict[str, Any]:
        """Gọi AI API (demo version)"""
        try:
            # DEMO: Trong thực tế cần gọi API thật
            # Ở đây tạo ảnh demo bằng PIL
            demo_image = self.create_demo_photo(prompt)
            return {
                'success': True,
                'image': demo_image,
                'message': 'Demo: Ảnh thẻ được tạo thành công!'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi API: {str(e)}'
            }
    
    def create_demo_photo(self, prompt: str) -> Image.Image:
        """Tạo ảnh demo bằng PIL"""
        # Tạo canvas trắng
        width, height = 400, 600  # 4x6 aspect ratio
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Vẽ border
        draw.rectangle([10, 10, width-10, height-10], outline='#DDDDDD', width=2)
        
        # Vẽ avatar (hình tròn)
        center_x, center_y = width // 2, height // 2 - 50
        radius = 80
        
        # Nền avatar
        draw.ellipse([center_x - radius, center_y - radius, 
                     center_x + radius, center_y + radius], 
                    fill='#F0F0F0', outline='#CCCCCC', width=2)
        
        # Vẽ mặt đơn giản
        # Mắt
        draw.ellipse([center_x - 35, center_y - 30, center_x - 15, center_y - 10], fill='#666666')
        draw.ellipse([center_x + 15, center_y - 30, center_x + 35, center_y - 10], fill='#666666')
        
        # Mũi
        draw.line([center_x, center_y - 5, center_x + 5, center_y + 10], fill='#999999', width=2)
        
        # Miệng (cười)
        draw.arc([center_x - 20, center_y + 10, center_x + 20, center_y + 50], 
                start=0, end=180, fill='#999999', width=3)
        
        # Trang phục
        if 'male' in prompt.lower():
            # Suit
            draw.rectangle([center_x - 60, center_y + radius - 10, 
                          center_x + 60, center_y + radius + 140], fill='#333333')
            # Cờ vạt
            draw.rectangle([center_x - 10, center_y + radius - 10,
                          center_x + 10, center_y + radius + 90], fill='#8B0000')
        else:
            # Blouse/Dress
            draw.rectangle([center_x - 70, center_y + radius - 10,
                          center_x + 70, center_y + radius + 140], fill='#4169E1')
        
        # Text thông tin
        try:
            # Sử dụng font mặc định nếu không tìm thấy font tùy chỉnh
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        except:
            font_large = None
            font_small = None
        
        # Thông tin ảnh thẻ
        gender_text = "Nam" if "male" in prompt.lower() else "Nữ"
        
        draw.text((center_x, height - 80), f"DEMO - Ảnh thẻ {gender_text}", 
                 fill='#666666', font=font_large, anchor="mm")
        draw.text((center_x, height - 60), "AI Generated", 
                 fill='#666666', font=font_small, anchor="mm")
        draw.text((center_x, height - 20), datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), 
                 fill='#CCCCCC', font=font_small, anchor="mm")
        
        return image

def main():
    """Hàm main của app"""
    
    # Header
    st.title("🎯 Tạo Ảnh Thẻ AI")
    st.markdown("### Tạo ảnh thẻ chuyên nghiệp với công nghệ Gemini 2.5 Flash")
    
    # Khởi tạo session state
    if 'photo_generator' not in st.session_state:
        st.session_state.photo_generator = IDPhotoGenerator()
    
    if 'generated_image' not in st.session_state:
        st.session_state.generated_image = None
        
    if 'options' not in st.session_state:
        st.session_state.options = {}
    
    # Layout chính
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Upload & Cấu hình")
        
        # File upload
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Chọn ảnh của bạn",
            type=['jpg', 'jpeg', 'png', 'webp', 'bmp'],
            help="Chấp nhận JPG, PNG, WEBP, BMP (Max 5MB)"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Preview ảnh
        if uploaded_file:
            validation = st.session_state.photo_generator.validate_image(uploaded_file)
            
            if validation['valid']:
                # Reset uploaded_file position
                uploaded_file.seek(0)
                image = Image.open(uploaded_file)
                
                st.success("✅ Ảnh hợp lệ!")
                st.image(image, caption=f"📁 {uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)", 
                        use_column_width=True)
                
                # File info
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("📏 Kích thước", f"{image.size[0]}x{image.size[1]}")
                with col_info2:
                    st.metric("📦 Dung lượng", f"{uploaded_file.size/1024:.1f} KB")
                with col_info3:
                    st.metric("🖼️ Định dạng", image.format or "Unknown")
                    
            else:
                st.error(f"❌ {validation['error']}")
                uploaded_file = None
    
    with col2:
        st.subheader("⚙️ Tùy chọn")
        
        # Chọn giới tính
        gender = st.radio("👤 Giới tính:", ("Nam", "Nữ"), horizontal=True)
        gender_key = "male" if gender == "Nam" else "female"
        
        # Kích thước ảnh thẻ
        photo_size = st.selectbox("📐 Kích thước ảnh thẻ:", 
                                 ["4x6 (10x15cm)", "3x4 (7.5x10cm)", "2x3 (5x7.5cm)"])
        
        # Options theo giới tính
        if gender == "Nam":
            st.markdown("#### 👨 Tùy chọn cho Nam")
            
            suit_style = st.selectbox("👔 Kiểu áo vest:", 
                                     ["Vest cổ điển", "Vest hiện đại", "Vest ôm body"])
            suit_color = st.selectbox("🎨 Màu áo vest:", 
                                     ["Xanh navy", "Đen", "Xám", "Xám đen"])
            tie_style = st.selectbox("👔 Cờ vạt:", 
                                    ["Cờ vạt trơn", "Cờ vạt sọc", "Cờ vạt chấm bi"])
            
            st.session_state.options = {
                'photo_size': photo_size.split()[0],
                'suit_style': suit_style.lower().replace(' ', '_'),
                'suit_color': suit_color.lower().replace(' ', '_'),
                'tie_style': tie_style.lower().replace(' ', '_')
            }
            
        else:  # Nữ
            st.markdown("#### 👩 Tùy chọn cho Nữ")
            
            female_outfit = st.selectbox("👗 Trang phục:", 
                                        ["Áo blazer", "Áo sơ mi", "Váy công sở", "Áo len"])
            female_color = st.selectbox("🎨 Màu trang phục:", 
                                       ["Trắng", "Đen", "Xanh navy", "Hồng", "Xanh dương"])
            background = st.selectbox("🖼️ Nền ảnh:", 
                                     ["Nền trắng", "Nền xanh dương", "Nền xám", "Nền gradient"])
            
            st.session_state.options = {
                'photo_size': photo_size.split()[0],
                'female_outfit': female_outfit.lower().replace(' ', '_'),
                'female_color': female_color.lower().replace(' ', '_'),
                'background': background.lower().replace(' ', '_')
            }
    
    # Nút Generate (full width)
    st.markdown("---")
    
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    with generate_col2:
        generate_btn = st.button("🚀 Tạo Ảnh Thẻ", 
                                type="primary", 
                                disabled=not uploaded_file,
                                help="Tải ảnh lên để kích hoạt" if not uploaded_file else None)
    
    # Xử lý generate
    if generate_btn and uploaded_file:
        with st.spinner("⏳ Đang tạo ảnh thẻ của bạn..."):
            # Tạo prompt
            prompt = st.session_state.photo_generator.create_prompt(gender_key, st.session_state.options)
            
            # Convert image to base64
            uploaded_file.seek(0)
            img_bytes = uploaded_file.read()
            img_base64 = base64.b64encode(img_bytes).decode()
            
            # Gọi API
            result = st.session_state.photo_generator.call_ai_api(prompt, img_base64)
            
            if result['success']:
                st.session_state.generated_image = result['image']
                st.success(f"✅ {result['message']}")
            else:
                st.error(f"❌ {result['error']}")
    
    # Hiển thị kết quả
    if st.session_state.generated_image:
        st.markdown("---")
        st.subheader("📸 Kết quả")
        
        result_col1, result_col2 = st.columns([2, 1])
        
        with result_col1:
            st.image(st.session_state.generated_image, 
                    caption="Ảnh thẻ AI đã tạo", 
                    use_column_width=True)
        
        with result_col2:
            # Thông tin ảnh
            st.markdown("#### 📊 Thông tin")
            st.info(f"""
            🎯 **Kích thước**: {st.session_state.options.get('photo_size', '4x6')}
            👤 **Giới tính**: {gender}
            ⏰ **Thời gian tạo**: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
            """)
            
            # Nút actions
            st.markdown("#### 🎬 Hành động")
            
            # Convert PIL Image to bytes for download
            img_buffer = io.BytesIO()
            st.session_state.generated_image.save(img_buffer, format='JPEG', quality=95)
            img_bytes = img_buffer.getvalue()
            
            # Download button
            st.download_button(
                label="📥 Tải xuống",
                data=img_bytes,
                file_name=f"id_photo_{gender_key}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg",
                type="primary"
            )
            
            # Reset button
            if st.button("🔄 Tạo lại", type="secondary"):
                st.session_state.generated_image = None
                st.experimental_rerun()
    
    # Sidebar với thông tin
    with st.sidebar:
        st.markdown("### 🛠️ Hướng dẫn sử dụng")
        st.markdown("""
        1. **📸 Tải ảnh lên**: Chọn file ảnh (JPG, PNG, WEBP)
        2. **👤 Chọn giới tính**: Nam hoặc Nữ  
        3. **⚙️ Tùy chỉnh**: Chọn trang phục, màu sắc, nền
        4. **🚀 Tạo ảnh**: Click nút "Tạo Ảnh Thẻ"
        5. **📥 Tải xuống**: Save ảnh về máy
        """)
        
        st.markdown("---")
        st.markdown("### 📋 Thông số kỹ thuật")
        st.markdown("""
        - **Định dạng hỗ trợ**: JPG, PNG, WEBP, BMP
        - **Kích thước tối đa**: 5MB
        - **Kích thước ảnh thẻ**: 4x6, 3x4, 2x3
        - **Chất lượng đầu ra**: 300 DPI
        """)
        
        st.markdown("---")
        st.markdown("### ⚠️ Lưu ý")
        st.warning("""
        **Demo Mode**: Hiện tại đang chạy ở chế độ demo với ảnh mẫu. 
        Để sử dụng AI thật, cần cấu hình API key trong `API_CONFIG`.
        """)
        
        # API Status
        api_status = "🟡 Demo Mode" if API_CONFIG['api_key'] == 'YOUR_API_KEY_HERE' else "🟢 API Ready"
        st.markdown(f"**Trạng thái API**: {api_status}")

if __name__ == "__main__":
    main()
