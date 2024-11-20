import streamlit as st
import os
import tempfile
from pathlib import Path
import subprocess
import platform

def get_default_output_dir():
    """根据操作系统返回默认输出目录"""
    system = platform.system().lower()
    if system == 'windows':
        return 'C:\\'
    else:  # Linux 或 MacOS
        return '/root'

def run_docling_command(input_path, output_formats, use_ocr=True, output_dir=None):
    """执行docling命令行"""
    input_path = Path(input_path)
    cmd = ["docling", str(input_path)]
    
    # 从临时文件名中提取原始文件名
    original_filename = input_path.name.split('_', 1)[1] if '_' in input_path.name else input_path.name
    original_stem = Path(original_filename).stem
    
    # 存储所有输出文件路径
    output_files = []
    
    # 添加输出格式
    for fmt in output_formats:
        output_dir = output_dir if output_dir else get_default_output_dir()
        output_path = Path(output_dir) / f"{original_stem}.{fmt}"
        cmd.extend(["--to", fmt])
        cmd.extend(["--output", str(output_path)])
        output_files.append(output_path)
    
    # OCR选项
    if not use_ocr:
        cmd.append("--no-ocr")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout, output_files
        else:
            return False, result.stderr, []
    except Exception as e:
        return False, str(e), []

def convert_file(input_file, output_path):
    try:
        # 确保输出路径存在
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                st.error("保存路径无法创建，请检查权限或选择其他位置")
                return False
            
        # 执行文件转换
        # ... 原有的转换代码 ...
        
        return True
        
    except FileNotFoundError:
        st.error("保存路径不存在，请选择有效的保存位置")
        return False
    except PermissionError:
        st.error("没有写入权限，请选择其他保存位置")
        return False
    except OSError as e:
        if "Read-only file system" in str(e):
            st.error("无法写入该位置，请选择其他保存位置")
        else:
            st.error("保存失败，请检查保存路径是否有效")
        return False
    except Exception as e:
        st.error("转换失败，请检查文件格式是否正确")
        return False

def main():
    st.title("Docling 文档转换工具")
    
    # 文件上传部分
    uploaded_files = st.file_uploader(
        "上传文件 (支持PDF和DOCX格式)", 
        accept_multiple_files=True,
        type=['pdf', 'docx']
    )
    
    # 输出格式选择
    output_formats = st.multiselect(
        "选择输出格式",
        options=["md", "json"],
        default=["md"],
        help="可以选择一个或多个输出格式"
    )
    
    # OCR选项
    use_ocr = st.checkbox("使用OCR", value=True, help="对PDF文件使用光学字符识别")
    
    # 获取默认输出目录
    default_output_dir = get_default_output_dir()
    
    # 输出目录
    output_dir = st.text_input(
        "输出目录",
        value=default_output_dir,
        help=f"默认输出目录：{default_output_dir}"
    )
    
    if st.button("开始转换"):
        if not uploaded_files:
            st.error("请先上传文件")
            return
        
        if not output_formats:
            st.error("请至少选择一种输出格式")
            return
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 处理每个上传的文件
        for i, uploaded_file in enumerate(uploaded_files):
            progress = (i + 1) / len(uploaded_files)
            status_text.text(f"正在处理: {uploaded_file.name}")
            
            # 创建临时文件，保持原始文件名
            original_filename = uploaded_file.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{original_filename}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # 执行转换
            success, message, output_files = run_docling_command(
                tmp_path,
                output_formats,
                use_ocr,
                output_dir if output_dir else None
            )
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            # 更新进度
            progress_bar.progress(progress)
            
            # 显示结果
            if success:
                # 合并成功消息和文件路径为一条消息
                for output_file in output_files:
                    st.success(f"{original_filename} 转换成功，已生成文件：{output_file}")
            else:
                st.error(f"{original_filename} 转换失败: {message}")
        
        # 完成处理
        status_text.text("所有文件处理完成")
        progress_bar.progress(1.0)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        sys.argv.extend(["--server.port", "6006"])
    main()
