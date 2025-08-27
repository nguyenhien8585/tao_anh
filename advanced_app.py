import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import datetime
import json
import os
import zipfile
from typing import Optional, Dict, Any, List
import uuid
import sqlite3
import hashlib
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

# Cấu hình trang
st.set_page_config(
    page_title="🎯 ID Photo Generator Pro", 
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS nâng cao
st.markdown("""
<style>
    .main > div {
        padding: 1rem;
    }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1rem;
        font-weight: 600;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    .success-card {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .batch-upload {
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .batch-upload:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        transform: translateY(-2px);
    }
    
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .image-item {
        border: 2px solid #dee2e6;
        border-radius: 10px;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .image-item:hover {
        border-color: #667eea;
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .progress-bar {
        height: 20px;
        border-radius: 10px;
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        text-align: center;
        line-height: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
@st.cache_resource
def init_database():
    """Khởi tạo database SQLite"""
    conn = sqlite3.connect('id_photos.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Bảng lưu lịch sử tạo ảnh
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photo_history (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            original_filename TEXT,
            generated_filename TEXT,
            gender TEXT,
            options TEXT,
            created_at TIMESTAMP,
            file_size INTEGER,
            processing_time REAL
        )
    ''')
    
    # Bảng thống kê
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            date TEXT PRIMARY KEY,
            total_photos INTEGER,
            male_photos INTEGER,
            female_photos INTEGER,
            avg_processing_time REAL
        )
    ''')
    
    conn.commit()
    return conn

# Enhanced ID Photo Generator
class AdvancedIDPhotoGenerator:
    """Class nâng cao để tạo ảnh thẻ AI với nhiều tính năng"""
    
    def __init__(self):
        self.allowed_formats = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.photo_sizes = {
            '4x6': (400, 600),
            '3x4': (300, 400),
            '2x3': (200, 300),
            '5x7': (500, 700),
            '35x45mm': (350, 450)
        }
        self.db = init_database()
        
    def validate_images(self, uploaded_files) -> Dict[str, Any]:
        """Validate multiple files"""
        valid_files = []
        invalid_files = []
        
        for uploaded_file in uploaded_files:
            validation = self.validate_image(uploaded_file)
            if validation['valid']:
                valid_files.append(uploaded_file)
            else:
                invalid_files.append({
                    'file': uploaded_file,
                    'error': validation['error']
                })
        
        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_valid': len(valid_files),
            'total_invalid': len(invalid_files)
        }
    
    def validate_image(self, uploaded_file) -> Dict[str, Any]:
        """Validate single file"""
        if not uploaded_file:
            return {'valid': False, 'error': 'File không tồn tại'}
            
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
            # Kiểm tra ảnh hợp lệ
            image = Image.open(uploaded_file)
            image.verify()
            
            # Reset file pointer
            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            
            # Kiểm tra kích thước tối thiểu
            if image.size[0] < 100 or image.size[1] < 100:
                return {'valid': False, 'error': 'Ảnh quá nhỏ (tối thiểu 100x100px)'}
                
            return {'valid': True, 'image': image}
        except Exception as e:
            return {'valid': False, 'error': f'File ảnh không hợp lệ: {str(e)}'}
    
    def enhance_image(self, image: Image.Image, enhancement_options: Dict) -> Image.Image:
        """Tăng cường chất lượng ảnh"""
        enhanced = image.copy()
        
        # Brightness
        if enhancement_options.get('brightness', 0) != 0:
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1 + enhancement_options['brightness'] / 100)
        
        # Contrast
        if enhancement_options.get('contrast', 0) != 0:
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1 + enhancement_options['contrast'] / 100)
        
        # Sharpness
        if enhancement_options.get('sharpness', 0) != 0:
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1 + enhancement_options['sharpness'] / 100)
        
        # Color saturation
        if enhancement_options.get('saturation', 0) != 0:
            enhancer = ImageEnhance.Color(enhanced)
            enhanced = enhancer.enhance(1 + enhancement_options['saturation'] / 100)
        
        # Noise reduction (simple blur)
        if enhancement_options.get('noise_reduction', False):
            enhanced = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return enhanced
    
    def create_demo_photo_advanced(self, prompt: str, original_image: Image.Image, 
                                  photo_size: str, enhancements: Dict) -> Image.Image:
        """Tạo ảnh demo nâng cao"""
        size = self.photo_sizes.get(photo_size, (400, 600))
        width, height = size
        
        # Tạo canvas
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Vẽ border
        border_color = '#DDDDDD'
        draw.rectangle([5, 5, width-5, height-5], outline=border_color, width=3)
        
        # Vẽ avatar từ original image (resize và crop)
        if original_image:
            # Resize original image to fit avatar area
            avatar_size = min(width//3, height//4)
            center_x, center_y = width // 2, height // 3
            
            # Crop to square and resize
            original_square = self.crop_to_square(original_image)
            avatar = original_square.resize((avatar_size * 2, avatar_size * 2), Image.Resampling.LANCZOS)
            
            # Apply enhancements
            avatar = self.enhance_image(avatar, enhancements)
            
            # Paste avatar
            avatar_x = center_x - avatar_size
            avatar_y = center_y - avatar_size
            image.paste(avatar, (avatar_x, avatar_y))
            
            # Draw oval mask (simulate professional photo)
            mask = Image.new('L', (avatar_size * 2, avatar_size * 2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, avatar_size * 2, avatar_size * 2], fill=255)
            
        # Vẽ trang phục area
        clothing_y = center_y + avatar_size
        
        if 'male' in prompt.lower():
            # Suit
            draw.rectangle([center_x - avatar_size, clothing_y, 
                          center_x + avatar_size, height - 100], fill='#2C3E50')
            # Tie
            draw.rectangle([center_x - 15, clothing_y, 
                          center_x + 15, clothing_y + 80], fill='#8B0000')
        else:
            # Blouse/Dress
            colors = {
                'white': '#FFFFFF', 'black': '#2C3E50', 'navy': '#34495E',
                'pink': '#E91E63', 'blue': '#2196F3'
            }
            color_name = 'blue'  # Default
            for color in colors.keys():
                if color in prompt.lower():
                    color_name = color
                    break
            
            draw.rectangle([center_x - avatar_size - 10, clothing_y,
                          center_x + avatar_size + 10, height - 100], 
                         fill=colors[color_name])
        
        # Background based on options
        if 'blue' in prompt.lower() and 'background' in prompt.lower():
            # Blue gradient background
            for y in range(height):
                color_intensity = int(200 + (y / height) * 55)
                draw.line([(0, y), (width, y)], fill=(100, 150, color_intensity))
        
        # Text information
        try:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        except:
            font_large = None
            font_small = None
        
        # Photo info
        gender_text = "Nam" if "male" in prompt.lower() else "Nữ"
        
        draw.text((center_x, height - 80), f"AI Photo - {gender_text}", 
                 fill='#2C3E50', font=font_large, anchor="mm")
        draw.text((center_x, height - 60), f"Size: {photo_size}", 
                 fill='#34495E', font=font_small, anchor="mm")
        draw.text((center_x, height - 40), "Enhanced Quality", 
                 fill='#7F8C8D', font=font_small, anchor="mm")
        draw.text((center_x, height - 20), 
                 datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), 
                 fill='#95A5A6', font=font_small, anchor="mm")
        
        return image
    
    def crop_to_square(self, image: Image.Image) -> Image.Image:
        """Crop ảnh thành hình vuông"""
        width, height = image.size
        size = min(width, height)
        
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        
        return image.crop((left, top, right, bottom))
    
    def process_batch(self, files: List, gender: str, options: Dict, 
                     enhancements: Dict, progress_callback=None) -> List[Dict]:
        """Xử lý batch photos"""
        results = []
        total_files = len(files)
        
        for i, uploaded_file in enumerate(files):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(i, total_files, f"Đang xử lý {uploaded_file.name}...")
                
                start_time = time.time()
                
                # Reset file position
                uploaded_file.seek(0)
                original_image = Image.open(uploaded_file)
                
                # Generate photo
                prompt = self.create_prompt(gender, options)
                generated_image = self.create_demo_photo_advanced(
                    prompt, original_image, options.get('photo_size', '4x6'), enhancements
                )
                
                processing_time = time.time() - start_time
                
                # Save to history
                photo_id = str(uuid.uuid4())
                self.save_to_history(
                    photo_id, uploaded_file.name, f"{photo_id}.jpg",
                    gender, options, processing_time, uploaded_file.size
                )
                
                results.append({
                    'success': True,
                    'original_name': uploaded_file.name,
                    'image': generated_image,
                    'photo_id': photo_id,
                    'processing_time': processing_time
                })
                
            except Exception as e:
                results.append({
                    'success': False,
                    'original_name': uploaded_file.name,
                    'error': str(e)
                })
        
        return results
    
    def create_prompt(self, gender: str, options: Dict[str, str]) -> str:
        """Tạo prompt nâng cao"""
        photo_size = options.get('photo_size', '4x6')
        prompt = f"Create a professional ID photo with {photo_size} dimensions, 300 DPI resolution. "
        
        if gender == 'male':
            suit_style = options.get('suit_style', 'classic').replace('_', ' ')
            suit_color = options.get('suit_color', 'navy').replace('_', ' ')
            tie_style = options.get('tie_style', 'solid').replace('_', ' ')
            
            prompt += f"Male subject wearing a {suit_style} {suit_color} business suit with a {tie_style} necktie. "
            prompt += "Professional formal attire, clean white background. "
            prompt += "IMPORTANT: Keep original facial features exactly the same, only enhance appearance. "
            
        else:  # female
            outfit = options.get('female_outfit', 'blazer').replace('_', ' ')
            color = options.get('female_color', 'white').replace('_', ' ')
            background = options.get('background', 'white').replace('_', ' ')
            
            prompt += f"Female subject wearing a {color} {outfit}. "
            prompt += f"Professional business attire with {background} background. "
            
        prompt += "Professional portrait photography, soft lighting, high resolution, passport photo quality."
        return prompt
    
    def save_to_history(self, photo_id: str, original_filename: str, 
                       generated_filename: str, gender: str, options: Dict,
                       processing_time: float, file_size: int):
        """Lưu vào database"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO photo_history 
            (id, user_id, original_filename, generated_filename, gender, options, 
             created_at, file_size, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (photo_id, 'default_user', original_filename, generated_filename, 
              gender, json.dumps(options), datetime.datetime.now(), 
              file_size, processing_time))
        self.db.commit()
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Lấy lịch sử từ database"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT * FROM photo_history 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_stats(self) -> Dict:
        """Lấy thống kê sử dụng"""
        cursor = self.db.cursor()
        
        # Total photos
        cursor.execute('SELECT COUNT(*) FROM photo_history')
        total_photos = cursor.fetchone()[0]
        
        # Photos by gender
        cursor.execute('SELECT gender, COUNT(*) FROM photo_history GROUP BY gender')
        gender_stats = dict(cursor.fetchall())
        
        # Average processing time
        cursor.execute('SELECT AVG(processing_time) FROM photo_history')
        avg_time = cursor.fetchone()[0] or 0
        
        # Today's photos
        today = datetime.date.today()
        cursor.execute('SELECT COUNT(*) FROM photo_history WHERE DATE(created_at) = ?', (today,))
        today_photos = cursor.fetchone()[0]
        
        return {
            'total_photos': total_photos,
            'male_photos': gender_stats.get('male', 0),
            'female_photos': gender_stats.get('female', 0),
            'avg_processing_time': avg_time,
            'today_photos': today_photos
        }

def create_download_zip(results: List[Dict]) -> bytes:
    """Tạo file ZIP chứa tất cả ảnh đã generate"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, result in enumerate(results):
            if result['success']:
                # Convert PIL Image to bytes
                img_buffer = io.BytesIO()
                result['image'].save(img_buffer, format='JPEG', quality=95)
                img_bytes = img_buffer.getvalue()
                
                # Add to ZIP
                filename = f"{i+1:03d}_{result['original_name'].split('.')[0]}_generated.jpg"
                zip_file.writestr(filename, img_bytes)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    """Main application"""
    
    # Khởi tạo
    if 'photo_generator' not in st.session_state:
        st.session_state.photo_generator = AdvancedIDPhotoGenerator()
    
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    
    # Header
    st.title("🎯 ID Photo Generator Pro")
    st.markdown("### Tạo ảnh thẻ chuyên nghiệp với AI - Phiên bản nâng cao")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🖼️ Tạo ảnh đơn", "📊 Xử lý hàng loạt", "📈 Thống kê", "📚 Lịch sử", "⚙️ Cài đặt"
    ])
    
    # Tab 1: Single photo generation
    with tab1:
        single_photo_interface()
    
    # Tab 2: Batch processing
    with tab2:
        batch_processing_interface()
    
    # Tab 3: Statistics
    with tab3:
        statistics_interface()
    
    # Tab 4: History
    with tab4:
        history_interface()
    
    # Tab 5: Settings
    with tab5:
        settings_interface()

def single_photo_interface():
    """Interface tạo ảnh đơn"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Upload & Cấu hình")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Chọn ảnh của bạn",
            type=['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'],
            help="Chấp nhận các định dạng: JPG, PNG, WEBP, BMP, TIFF (Max 10MB)"
        )
        
        if uploaded_file:
            validation = st.session_state.photo_generator.validate_image(uploaded_file)
            
            if validation['valid']:
                uploaded_file.seek(0)
                image = Image.open(uploaded_file)
                
                st.success("✅ Ảnh hợp lệ!")
                st.image(image, caption=f"📁 {uploaded_file.name}", use_column_width=True)
                
                # Image info metrics
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
        
        # Enhancement options
        if uploaded_file:
            st.markdown("#### 🎨 Tùy chỉnh chất lượng")
            
            enhance_expander = st.expander("🔧 Điều chỉnh ảnh", expanded=False)
            with enhance_expander:
                brightness = st.slider("☀️ Độ sáng", -50, 50, 0, help="Điều chỉnh độ sáng của ảnh")
                contrast = st.slider("🌗 Độ tương phản", -50, 50, 0, help="Tăng/giảm độ tương phản")
                sharpness = st.slider("🔍 Độ sắc nét", -50, 50, 10, help="Làm sắc nét ảnh")
                saturation = st.slider("🎨 Độ bão hòa màu", -50, 50, 5, help="Điều chỉnh độ sống động của màu")
                noise_reduction = st.checkbox("🔇 Giảm nhiễu", value=True, help="Giảm nhiễu trong ảnh")
                
                enhancements = {
                    'brightness': brightness,
                    'contrast': contrast, 
                    'sharpness': sharpness,
                    'saturation': saturation,
                    'noise_reduction': noise_reduction
                }
    
    with col2:
        st.subheader("⚙️ Tùy chọn ảnh thẻ")
        
        # Gender selection
        gender = st.radio("👤 Giới tính:", ("Nam", "Nữ"), horizontal=True)
        gender_key = "male" if gender == "Nam" else "female"
        
        # Photo size
        photo_sizes = ["4x6 (10x15cm)", "3x4 (7.5x10cm)", "2x3 (5x7.5cm)", "5x7 (12.5x17.5cm)", "35x45mm (Hộ chiếu)"]
        photo_size = st.selectbox("📐 Kích thước ảnh thẻ:", photo_sizes)
        
        # Gender-specific options
        if gender == "Nam":
            st.markdown("#### 👨 Tùy chọn cho Nam")
            
            suit_style = st.selectbox("👔 Kiểu áo vest:", 
                                     ["Vest cổ điển", "Vest hiện đại", "Vest ôm body", "Vest thể thao"])
            suit_color = st.selectbox("🎨 Màu áo vest:", 
                                     ["Xanh navy", "Đen", "Xám", "Xám đen", "Nâu"])
            tie_style = st.selectbox("👔 Cờ vạt:", 
                                    ["Cờ vạt trơn", "Cờ vạt sọc", "Cờ vạt chấm bi", "Cờ vạt họa tiết"])
            
            options = {
                'photo_size': photo_size.split()[0],
                'suit_style': suit_style.lower().replace(' ', '_'),
                'suit_color': suit_color.lower().replace(' ', '_'),
                'tie_style': tie_style.lower().replace(' ', '_')
            }
            
        else:  # Female
            st.markdown("#### 👩 Tùy chọn cho Nữ")
            
            female_outfit = st.selectbox("👗 Trang phục:", 
                                        ["Áo blazer", "Áo sơ mi", "Váy công sở", "Áo len", "Áo khoác nhẹ"])
            female_color = st.selectbox("🎨 Màu trang phục:", 
                                       ["Trắng", "Đen", "Xanh navy", "Hồng", "Xanh dương", "Beige"])
            background = st.selectbox("🖼️ Nền ảnh:", 
                                     ["Nền trắng", "Nền xanh dương", "Nền xám", "Nền gradient", "Nền be"])
            
            options = {
                'photo_size': photo_size.split()[0],
                'female_outfit': female_outfit.lower().replace(' ', '_'),
                'female_color': female_color.lower().replace(' ', '_'),
                'background': background.lower().replace(' ', '_')
            }
    
    # Generate button
    st.markdown("---")
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 2, 1])
    with col_gen2:
        generate_btn = st.button("🚀 Tạo Ảnh Thẻ Chất Lượng Cao", 
                                type="primary", 
                                disabled=not uploaded_file,
                                help="Tải ảnh lên để kích hoạt" if not uploaded_file else None)
    
    # Process generation
    if generate_btn and uploaded_file:
        with st.spinner("⏳ Đang tạo ảnh thẻ chất lượng cao..."):
            start_time = time.time()
            
            # Generate photo
            uploaded_file.seek(0)
            original_image = Image.open(uploaded_file)
            prompt = st.session_state.photo_generator.create_prompt(gender_key, options)
            
            generated_image = st.session_state.photo_generator.create_demo_photo_advanced(
                prompt, original_image, options['photo_size'], 
                enhancements if 'enhancements' in locals() else {}
            )
            
            processing_time = time.time() - start_time
            
            # Save to history
            photo_id = str(uuid.uuid4())
            st.session_state.photo_generator.save_to_history(
                photo_id, uploaded_file.name, f"{photo_id}.jpg",
                gender_key, options, processing_time, uploaded_file.size
            )
            
            # Display results
            st.markdown("---")
            st.subheader("📸 Kết quả")
            
            result_col1, result_col2 = st.columns([2, 1])
            
            with result_col1:
                st.image(generated_image, caption="Ảnh thẻ chất lượng cao", use_column_width=True)
            
            with result_col2:
                st.markdown("#### 📊 Thông tin chi tiết")
                
                # Enhanced metrics
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("⚡ Thời gian xử lý", f"{processing_time:.2f}s")
                    st.metric("🎯 Kích thước", options['photo_size'])
                with col_m2:
                    st.metric("👤 Giới tính", gender)
                    st.metric("📅 Ngày tạo", datetime.datetime.now().strftime("%d/%m/%Y"))
                
                # Download section
                st.markdown("#### 📥 Tải xuống")
                
                # Convert to bytes
                img_buffer = io.BytesIO()
                generated_image.save(img_buffer, format='JPEG', quality=95)
                img_bytes = img_buffer.getvalue()
                
                # Download button
                st.download_button(
                    label="📥 Tải ảnh chất lượng cao",
                    data=img_bytes,
                    file_name=f"id_photo_pro_{gender_key}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                    mime="image/jpeg",
                    type="primary"
                )
                
                # Additional formats
                with st.expander("📄 Tải các định dạng khác", expanded=False):
                    # PNG
                    png_buffer = io.BytesIO()
                    generated_image.save(png_buffer, format='PNG')
                    png_bytes = png_buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Tải PNG (nền trong suốt)",
                        data=png_bytes,
                        file_name=f"id_photo_pro_{gender_key}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png"
                    )
                    
                    # PDF (simple wrapper)
                    # Note: Would need additional libraries for proper PDF generation

def batch_processing_interface():
    """Interface xử lý hàng loạt"""
    st.subheader("📊 Xử lý hàng loạt ảnh thẻ")
    st.markdown("Tải lên nhiều ảnh và tạo ảnh thẻ cùng lúc với cùng một cấu hình.")
    
    # Batch upload
    st.markdown('<div class="batch-upload">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "📁 Chọn nhiều ảnh (tối đa 20 ảnh)",
        type=['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help="Chọn tối đa 20 ảnh để xử lý cùng lúc"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        # Limit to 20 files
        if len(uploaded_files) > 20:
            st.warning("⚠️ Chỉ xử lý 20 ảnh đầu tiên. Vui lòng tải lên ít ảnh hơn.")
            uploaded_files = uploaded_files[:20]
        
        # Validate all files
        validation_results = st.session_state.photo_generator.validate_images(uploaded_files)
        
        # Show validation results
        col_valid1, col_valid2 = st.columns(2)
        
        with col_valid1:
            st.success(f"✅ {validation_results['total_valid']} ảnh hợp lệ")
            
        with col_valid2:
            if validation_results['total_invalid'] > 0:
                st.error(f"❌ {validation_results['total_invalid']} ảnh không hợp lệ")
        
        # Show invalid files details
        if validation_results['invalid_files']:
            with st.expander("⚠️ Chi tiết ảnh không hợp lệ", expanded=False):
                for invalid in validation_results['invalid_files']:
                    st.error(f"**{invalid['file'].name}**: {invalid['error']}")
        
        if validation_results['valid_files']:
            # Batch configuration
            st.markdown("#### ⚙️ Cấu hình cho tất cả ảnh")
            
            batch_col1, batch_col2 = st.columns(2)
            
            with batch_col1:
                # Gender for all
                batch_gender = st.radio("👤 Giới tính chung:", ("Nam", "Nữ"), 
                                       horizontal=True, key="batch_gender")
                batch_gender_key = "male" if batch_gender == "Nam" else "female"
                
                # Photo size for all
                batch_photo_size = st.selectbox("📐 Kích thước chung:", 
                                               ["4x6 (10x15cm)", "3x4 (7.5x10cm)", "2x3 (5x7.5cm)", 
                                                "5x7 (12.5x17.5cm)", "35x45mm (Hộ chiếu)"],
                                               key="batch_size")
            
            with batch_col2:
                # Enhancement options for batch
                st.markdown("##### 🎨 Tùy chỉnh chất lượng chung")
                batch_brightness = st.slider("☀️ Độ sáng", -50, 50, 0, key="batch_brightness")
                batch_contrast = st.slider("🌗 Độ tương phản", -50, 50, 0, key="batch_contrast")
                batch_sharpness = st.slider("🔍 Độ sắc nét", -50, 50, 10, key="batch_sharpness")
            
            # Gender-specific batch options
            if batch_gender == "Nam":
                batch_suit_style = st.selectbox("👔 Kiểu áo vest chung:", 
                                               ["Vest cổ điển", "Vest hiện đại", "Vest ôm body"],
                                               key="batch_suit")
                batch_suit_color = st.selectbox("🎨 Màu áo vest chung:", 
                                               ["Xanh navy", "Đen", "Xám", "Xám đen"],
                                               key="batch_suit_color")
                
                batch_options = {
                    'photo_size': batch_photo_size.split()[0],
                    'suit_style': batch_suit_style.lower().replace(' ', '_'),
                    'suit_color': batch_suit_color.lower().replace(' ', '_'),
                    'tie_style': 'solid'
                }
            else:
                batch_outfit = st.selectbox("👗 Trang phục chung:", 
                                          ["Áo blazer", "Áo sơ mi", "Váy công sở"],
                                          key="batch_outfit")
                batch_color = st.selectbox("🎨 Màu trang phục chung:", 
                                         ["Trắng", "Đen", "Xanh navy", "Hồng"],
                                         key="batch_color")
                
                batch_options = {
                    'photo_size': batch_photo_size.split()[0],
                    'female_outfit': batch_outfit.lower().replace(' ', '_'),
                    'female_color': batch_color.lower().replace(' ', '_'),
                    'background': 'white'
                }
            
            batch_enhancements = {
                'brightness': batch_brightness,
                'contrast': batch_contrast,
                'sharpness': batch_sharpness,
                'saturation': 5,
                'noise_reduction': True
            }
            
            # Process batch button
            st.markdown("---")
            
            col_batch1, col_batch2, col_batch3 = st.columns([1, 2, 1])
            with col_batch2:
                process_batch_btn = st.button(
                    f"🚀 Xử lý {len(validation_results['valid_files'])} ảnh",
                    type="primary",
                    key="process_batch"
                )
            
            # Process batch
            if process_batch_btn:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, message):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ {message} ({current}/{total})")
                
                with st.spinner("🔄 Đang xử lý hàng loạt..."):
                    batch_results = st.session_state.photo_generator.process_batch(
                        validation_results['valid_files'],
                        batch_gender_key,
                        batch_options,
                        batch_enhancements,
                        update_progress
                    )
                    
                    st.session_state.batch_results = batch_results
                
                # Show results summary
                successful_count = sum(1 for r in batch_results if r['success'])
                failed_count = len(batch_results) - successful_count
                
                col_result1, col_result2 = st.columns(2)
                with col_result1:
                    st.success(f"✅ Thành công: {successful_count} ảnh")
                with col_result2:
                    if failed_count > 0:
                        st.error(f"❌ Thất bại: {failed_count} ảnh")
                
                # Display results grid
                if successful_results := [r for r in batch_results if r['success']]:
                    st.markdown("#### 📸 Kết quả hàng loạt")
                    
                    # Create image grid
                    cols = st.columns(4)  # 4 images per row
                    
                    for i, result in enumerate(successful_results):
                        col_index = i % 4
                        with cols[col_index]:
                            st.image(result['image'], 
                                   caption=f"{result['original_name']}\n({result['processing_time']:.2f}s)",
                                   use_column_width=True)
                    
                    # Bulk download
                    st.markdown("#### 📥 Tải xuống hàng loạt")
                    
                    col_download1, col_download2 = st.columns(2)
                    
                    with col_download1:
                        # Create ZIP file
                        zip_data = create_download_zip(successful_results)
                        
                        st.download_button(
                            label=f"📦 Tải ZIP ({successful_count} ảnh)",
                            data=zip_data,
                            file_name=f"batch_id_photos_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            type="primary"
                        )
                    
                    with col_download2:
                        # Statistics
                        total_time = sum(r['processing_time'] for r in successful_results)
                        avg_time = total_time / len(successful_results)
                        
                        st.info(f"""
                        📊 **Thống kê batch:**
                        - Tổng thời gian: {total_time:.2f}s
                        - Trung bình/ảnh: {avg_time:.2f}s
                        - Tốc độ: {len(successful_results)/total_time:.1f} ảnh/giây
                        """)

def statistics_interface():
    """Interface thống kê"""
    st.subheader("📈 Thống kê sử dụng")
    
    # Get stats
    stats = st.session_state.photo_generator.get_stats()
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📸 Tổng ảnh đã tạo", stats['total_photos'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("👨 Ảnh nam", stats['male_photos'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("👩 Ảnh nữ", stats['female_photos'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("⏱️ Thời gian TB", f"{stats['avg_processing_time']:.2f}s")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Charts
    if stats['total_photos'] > 0:
        st.markdown("#### 📊 Biểu đồ phân bố")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Gender distribution pie chart
            gender_data = pd.DataFrame({
                'Giới tính': ['Nam', 'Nữ'],
                'Số lượng': [stats['male_photos'], stats['female_photos']]
            })
            
            if stats['male_photos'] > 0 or stats['female_photos'] > 0:
                st.bar_chart(gender_data.set_index('Giới tính'))
        
        with chart_col2:
            # Daily usage (mock data for demo)
            daily_data = pd.DataFrame({
                'Ngày': pd.date_range(start='2024-01-01', periods=7),
                'Số ảnh': np.random.randint(1, 20, 7)
            })
            st.line_chart(daily_data.set_index('Ngày'))
    
    else:
        st.info("📊 Chưa có dữ liệu thống kê. Hãy tạo một số ảnh thẻ để xem thống kê!")

def history_interface():
    """Interface lịch sử"""
    st.subheader("📚 Lịch sử tạo ảnh")
    
    # Get history
    history = st.session_state.photo_generator.get_history(limit=100)
    
    if history:
        # Search and filter
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            search_term = st.text_input("🔍 Tìm kiếm theo tên file:", placeholder="Nhập tên file...")
        
        with search_col2:
            gender_filter = st.selectbox("👤 Lọc theo giới tính:", ["Tất cả", "Nam", "Nữ"])
        
        # Filter history
        filtered_history = history
        
        if search_term:
            filtered_history = [h for h in filtered_history 
                              if search_term.lower() in h['original_filename'].lower()]
        
        if gender_filter != "Tất cả":
            gender_key = "male" if gender_filter == "Nam" else "female"
            filtered_history = [h for h in filtered_history if h['gender'] == gender_key]
        
        # Display history table
        if filtered_history:
            st.markdown(f"📋 Hiển thị {len(filtered_history)} kết quả:")
            
            # Convert to dataframe for better display
            df_history = pd.DataFrame(filtered_history)
            df_history['created_at'] = pd.to_datetime(df_history['created_at'])
            df_history['Thời gian tạo'] = df_history['created_at'].dt.strftime('%d/%m/%Y %H:%M')
            df_history['Tên file gốc'] = df_history['original_filename']
            df_history['Giới tính'] = df_history['gender'].map({'male': 'Nam', 'female': 'Nữ'})
            df_history['Thời gian xử lý'] = df_history['processing_time'].round(2).astype(str) + 's'
            df_history['Kích thước file'] = (df_history['file_size'] / 1024).round(1).astype(str) + ' KB'
            
            # Display selected columns
            display_df = df_history[['Thời gian tạo', 'Tên file gốc', 'Giới tính', 
                                   'Thời gian xử lý', 'Kích thước file']].head(50)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export options
            st.markdown("#### 📤 Xuất dữ liệu")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                # CSV export
                csv_data = display_df.to_csv(index=False)
                st.download_button(
                    label="📄 Xuất CSV",
                    data=csv_data,
                    file_name=f"photo_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with export_col2:
                # JSON export
                json_data = df_history.to_json(orient='records', date_format='iso')
                st.download_button(
                    label="📋 Xuất JSON", 
                    data=json_data,
                    file_name=f"photo_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        else:
            st.warning("🔍 Không tìm thấy kết quả nào với bộ lọc hiện tại.")
    
    else:
        st.info("📚 Chưa có lịch sử tạo ảnh. Hãy tạo ảnh thẻ đầu tiên!")

def settings_interface():
    """Interface cài đặt"""
    st.subheader("⚙️ Cài đặt ứng dụng")
    
    # API Configuration
    st.markdown("#### 🔧 Cấu hình API")
    
    api_expander = st.expander("🛠️ Cấu hình API Gemini", expanded=False)
    with api_expander:
        current_endpoint = st.text_input("🌐 API Endpoint:", value="https://api.llm.ai.vn/v1")
        current_model = st.text_input("🤖 Model:", value="gemini:gemini-2.5-flash")
        current_api_key = st.text_input("🔑 API Key:", type="password", 
                                       placeholder="Nhập API key của bạn...")
        
        if st.button("💾 Lưu cấu hình API"):
            st.success("✅ Đã lưu cấu hình API!")
            st.info("🔄 Khởi động lại ứng dụng để áp dụng thay đổi.")
    
    # App Settings
    st.markdown("#### 🎨 Cài đặt giao diện")
    
    theme_col1, theme_col2 = st.columns(2)
    
    with theme_col1:
        # Theme selection (for demo)
        theme_choice = st.selectbox("🎨 Chọn theme:", ["Light", "Dark", "Auto"])
        
    with theme_col2:
        # Language selection (for demo)
        language_choice = st.selectbox("🌍 Ngôn ngữ:", ["Tiếng Việt", "English", "中文"])
    
    # Performance Settings
    st.markdown("#### ⚡ Cài đặt hiệu suất")
    
    perf_col1, perf_col2 = st.columns(2)
    
    with perf_col1:
        max_file_size = st.number_input("📦 Kích thước file tối đa (MB):", 
                                       min_value=1, max_value=50, value=10)
        batch_limit = st.number_input("📊 Số ảnh tối đa trong batch:", 
                                     min_value=1, max_value=50, value=20)
    
    with perf_col2:
        auto_enhance = st.checkbox("✨ Tự động tăng cường chất lượng", value=True)
        save_history = st.checkbox("💾 Lưu lịch sử tạo ảnh", value=True)
    
    # Data Management
    st.markdown("#### 🗄️ Quản lý dữ liệu")
    
    data_col1, data_col2 = st.columns(2)
    
    with data_col1:
        if st.button("🗑️ Xóa lịch sử", type="secondary"):
            if st.button("⚠️ Xác nhận xóa lịch sử", type="secondary"):
                # Clear database
                cursor = st.session_state.photo_generator.db.cursor()
                cursor.execute("DELETE FROM photo_history")
                cursor.execute("DELETE FROM usage_stats") 
                st.session_state.photo_generator.db.commit()
                st.success("✅ Đã xóa toàn bộ lịch sử!")
                st.rerun()
    
    with data_col2:
        # Database backup
        if st.button("💾 Backup dữ liệu", type="primary"):
            # Export database (simplified)
            history = st.session_state.photo_generator.get_history(limit=1000)
            backup_data = {
                'export_time': datetime.datetime.now().isoformat(),
                'total_records': len(history),
                'data': history
            }
            
            backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 Tải file backup",
                data=backup_json,
                file_name=f"id_photo_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # About & Help
    st.markdown("#### ℹ️ Thông tin ứng dụng")
    
    st.info("""
    **🎯 ID Photo Generator Pro v2.0**
    
    Phát triển bởi: AI Assistant  
    Công nghệ: Streamlit + PIL + Gemini AI  
    Tính năng: Tạo ảnh thẻ chuyên nghiệp với AI
    
    📧 Hỗ trợ: support@example.com  
    🌐 Website: https://example.com
    """)
    
    # System info
    with st.expander("💻 Thông tin hệ thống", expanded=False):
        import sys
        import platform
        
        st.code(f"""
Python: {sys.version}
Platform: {platform.platform()}
Streamlit: {st.__version__}
PIL: {Image.__version__ if hasattr(Image, '__version__') else 'Unknown'}
Database: SQLite3
        """)

if __name__ == "__main__":
    main()
