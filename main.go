package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	// وضع التوكن الخاص بك مباشرة هنا
	TOKEN := "8702404471:AAEm0MN-g1SNgpCZKSuWGTqfjc-FdDzZeRE"
	
	bot, err := tgbotapi.NewBotAPI(TOKEN)
	if err != nil {
		log.Fatal(err)
	}

	log.Println("🚀 Falcon-Bot شغال الآن...")

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message != nil {
			go handle(bot, update.Message)
		}
	}
}

func handle(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	url := msg.Text
	if url == "" {
		return
	}

	bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "⏬ جاري صيد الفيديو..."))

	filename := fmt.Sprintf("video_%d.mp4", time.Now().Unix())

	// تنفيذ أمر yt-dlp للتحميل
	cmd := exec.Command("yt-dlp", "-f", "best", "-o", filename, url)
	err := cmd.Run()
	if err != nil {
		bot.Send(tgbotapi.NewMessage(msg.Chat.ID, "❌ فشل التحميل، تأكد من صحة الرابط"))
		return
	}

	video := tgbotapi.NewVideo(msg.Chat.ID, tgbotapi.FilePath(filename))
	video.Caption = "✅ تم التحميل بواسطة Falcon-Bot"

	_, err = bot.Send(video)
	if err != nil {
		log.Println("Error sending video:", err)
	}

	// حذف الملف بعد الإرسال لتوفير المساحة على السيرفر
	os.Remove(filename)
}
