import streamlit as st
import os
import tempfile
from pathlib import Path
import subprocess
import platform

def get_default_output_dir():
    """返回项目的tmp目录"""
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    # 创建tmp目录
    tmp_dir = current_dir / 'tmp'
    tmp_dir.mkdir(exist_ok=True)
    return tmp_dir

def run_docling_command(input_path, output_formats, use_ocr=True):
    """执行docling命令行"""
    input_path = Path(input_path)
    cmd = ["docling", str(input_path)]
    
    # 从临时文件名中提取原始文件名
    original_filename = input_path.name.split('_', 1)[1] if '_' in input_path.name else input_path.name
    original_stem = Path(original_filename).stem
    
    # 存储所有输出文件路径
    output_files = []
    output_dir = get_default_output_dir()
    
    # 添加输出格式
    for fmt in output_formats:
        output_path = output_dir / f"{original_stem}.{fmt}"
        cmd.extend(["--to", fmt])
        cmd.extend(["--output", str(output_path)])
        # 如果是目录，找到目录中的实际文件
        if output_path.is_dir():
            # 查找目录中的对应格式文件
            files = list(output_path.glob(f"*.{fmt}"))
            if files:
                output_files.extend(files)
        else:
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
        
        # 存储所有生成的文件信息
        generated_files = []
        
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
                use_ocr
            )
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            # 更新进度
            progress_bar.progress(progress)
            
            # 显示结果
            if success:
                for output_file in output_files:
                    st.success(f"{original_filename} 转换成功，已生成文件：{output_file}")
                    # 将成功生成的文件添加到列表
                    generated_files.append(output_file)
            else:
                st.error(f"{original_filename} 转换失败: {message}")
        
        # 完成处理
        status_text.text("所有文件处理完成")
        progress_bar.progress(1.0)
        
        # 显示下载区域
        if generated_files:
            st.markdown("### 下载转换后的文件")
            for file_path in generated_files:
                try:
                    # 检查是否为目录
                    if file_path.is_dir():
                        # 如果是目录，找到目录中的所有文件
                        for actual_file in file_path.glob("*.*"):
                            with open(actual_file, 'rb') as f:
                                file_content = f.read()
                                file_name = actual_file.name
                                st.download_button(
                                    label=f"下载 {file_name}",
                                    data=file_content,
                                    file_name=file_name,
                                    mime='application/octet-stream'
                                )
                    else:
                        # 如果是文件，直接读取
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                            file_name = file_path.name
                            st.download_button(
                                label=f"下载 {file_name}",
                                data=file_content,
                                file_name=file_name,
                                mime='application/octet-stream'
                            )
                except Exception as e:
                    st.error(f"无法读取文件 {file_path}: {str(e)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        sys.argv.extend(["--server.port", "6006"])
    main()
