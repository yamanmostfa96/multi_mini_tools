import subprocess


# الأمر الذي نريد تنفيذه
command = "python -m auto_py_to_exe"

try:
    # تنفيذ الأمر..
    subprocess.run("python -m auto_py_to_exe", shell=True, check=True)

except subprocess.CalledProcessError as e:
    print(f"حدث خطأ أثناء تنفيذ الأمر: {str(e)}")
except Exception as e:
    print(f"حدث خطأ غير متوقع: {str(e)}")
