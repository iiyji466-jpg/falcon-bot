# استخدام صورة تحتوي على لغة Go
FROM golang:1.21-bullseye

# تثبيت Python و yt-dlp و ffmpeg اللازمة للتحميل والمعالجة
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# تثبيت أداة التحميل yt-dlp
RUN pip3 install yt-dlp

# إعداد مجلد العمل داخل السيرفر
WORKDIR /app

# نسخ ملفات المشروع (main.go وأي ملفات أخرى)
COPY . .

# تحميل المكتبات وبناء ملف التشغيل
RUN go mod init falcon-bot || true
RUN go mod tidy
RUN go build -o main .

# أمر تشغيل البوت
CMD ["./main"]
