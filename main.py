import feedparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
import time

# الرمز المميز للبوت
TELEGRAM_API_TOKEN = '6869763414:AAHYADOG7PhbAINNB7iqOyqyXAbfxNHdU2w'

# قائمة روابط الـ RSS
RSS_FEED_URLS = [
    'https://alwatannews.net/rssFeed/97',
    'https://www.aljazeera.net/xml/rss/all.xml',
    'https://www.alarabiya.net/.mrss/ar/iraq.xml',
]

# قائمة لحفظ المقالات التي تم نشرها بالفعل
published_articles = set()

# قائمة لحفظ المستخدمين الذين فعلوا الإشعارات
subscribed_users = set()

# قائمة لحفظ القنوات التي تم تفعيل الإشعارات بها
active_channels = set()

# معرف القناة للاشتراك
CHANNEL_USERNAME = "@MAX_PRO8"

# دالة لجلب الأخبار من RSS مع الصور والفيديوهات
def fetch_news():
    articles = []
    for url in RSS_FEED_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title not in published_articles:
                article = {
                    'title': entry.title,
                    'content': entry.content[0].value if 'content' in entry and entry.content else 
                               entry.description if 'description' in entry and entry.description else 
                               entry.summary,
                    'image': entry.media_content[0]['url'] if 'media_content' in entry else None,
                    'video': entry.media_thumbnail[0]['url'] if 'media_thumbnail' in entry else None
                }
                articles.append(article)
                published_articles.add(entry.title)
    return articles

# دالة لإرسال الأخبار
def send_news(context):
    bot = context.bot
    news = fetch_news()

    if news:
        for article in news:
            full_message = f"{article['title']}\n\n{article['content']}"
            keyboard = [[InlineKeyboardButton("مشاركة البوت", url="https://t.me/share/url?url=اليك%20بوت%20يقدم%20اخر%20الاخبار%20والمستجدات%20في%20العالم%20والشرق%20الاوسط%0A%0Aمعرف%20البوت%20:%20@Ourlambot")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            for chat_id in subscribed_users.union(active_channels):
                try:
                    if article['image']:
                        bot.send_photo(chat_id=chat_id, photo=article['image'], caption=full_message, reply_markup=reply_markup)
                    elif article['video']:
                        bot.send_video(chat_id=chat_id, video=article['video'], caption=full_message, reply_markup=reply_markup)
                    else:
                        bot.send_message(chat_id=chat_id, text=full_message, reply_markup=reply_markup)

                except Exception as e:
                    print(f"Error sending message to {chat_id}: {e}")

            time.sleep(20)
    else:
        print("No new articles to send.")

# دالة للتحقق من الاشتراك
def check_subscription(update, context):
    chat_id = update.effective_chat.id
    try:
        member = context.bot.get_chat_member(CHANNEL_USERNAME, chat_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# دالة لبدء البوت وإرسال رسالة البداية
def start(update, context):
    chat_id = update.effective_chat.id

    if not check_subscription(update, context):
        # رسالة الاشتراك
        subscription_message = """
مرحبًا بك في بوت الأخبار العربية!

للاستفادة من خدماتنا والحصول على آخر الأخبار والمستجدات، يتوجب عليك الاشتراك في قناتنا الرسمية:

الرجاء الضغط على الزر في الأسفل والاشتراك، ثم العودة هنا لتفعيل البوت. شكرًا لدعمك!
""" + CHANNEL_USERNAME
        
        keyboard = [[InlineKeyboardButton("اشتراك الآن", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # إرسال رسالة الاشتراك بدون صورة
        context.bot.send_message(chat_id=chat_id, text=subscription_message, reply_markup=reply_markup)
        return

    # إذا كان المستخدم مشتركًا، تابع مع الرسالة الترحيبية أو العمليات الأخرى هنا
    start_message = """
مرحبًا بك في بوت الأخبار العربية والعراقية!
سنقوم بإرسال آخر الأخبار لك بشكل منتظم. يغطي البوت الأخبار العربية والعراقية.
قم بتفعيل أو تعطيل الإشعارات أدناه.

شارك البوت مع أصدقائك : @Ourlambot
"""
    image_url = "https://j.top4top.io/p_3193w7paz1.jpg"
    keyboard = [
        [InlineKeyboardButton("تفعيل الإشعارات", callback_data='enable_notifications')],
        [InlineKeyboardButton("تعطيل الإشعارات", callback_data='disable_notifications')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=start_message, reply_markup=reply_markup)

# دالة لمعالجة الضغط على الأزرار (تفعيل/تعطيل الإشعارات)
def button(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id

    if query.data == 'enable_notifications':
        subscribed_users.add(chat_id)
        query.answer(text="تم تفعيل الإشعارات.")
    elif query.data == 'disable_notifications':
        if chat_id in subscribed_users:
            subscribed_users.remove(chat_id)
        query.answer(text="تم تعطيل الإشعارات.")

# دالة لمعالجة رسالة "تفعيل" لتفعيل الإشعارات في القناة
def activate_channel(update, context):
    chat_id = update.effective_chat.id

    if update.channel_post and update.channel_post.text.lower() == "تفعيل":
        if context.bot.get_chat_member(chat_id, context.bot.id).status in ['administrator', 'creator']:
            active_channels.add(chat_id)
            activation_message = """
تم تفعيل البوت بنجاح في هذه القناة!

لضمان عمل البوت بشكل صحيح، يرجى التأكد من منحه كافة الصلاحيات، بما في ذلك "نشر الرسائل".

سيتم نشر آخر الأخبار والمستجدات بشكل دوري.
"""
            commands_button = InlineKeyboardButton("", callback_data='show_commands')
            reply_markup = InlineKeyboardMarkup([[commands_button]])
            context.bot.send_message(chat_id=chat_id, text=activation_message, reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id, text="يجب أن أكون مشرفًا في القناة لتفعيل البوت.")

# دالة لإظهار أوامر البوت
def show_commands(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id

    member = context.bot.get_chat_member(chat_id, query.from_user.id)
    if member.status in ['administrator', 'creator']:
        commands_message = """
        أوامر البوت المتاحة:
        - /start: بدء التفاعل مع البوت
        - /help: عرض معلومات المساعدة
        - /subscribe: الاشتراك في الإشعارات
        - /unsubscribe: إلغاء الاشتراك في الإشعارات
        """
        context.bot.send_message(chat_id=chat_id, text=commands_message)
    else:
        context.bot.send_message(chat_id=chat_id, text="عذرًا، هذه الأوامر متاحة فقط للمشرفين.")

# دالة لعرض معلومات المساعدة
def help_command(update, context):
    help_message = """
    هذه معلومات المساعدة للبوت:
    - /start: بدء التفاعل مع البوت
    - /help: عرض معلومات المساعدة
    - /subscribe: الاشتراك في الإشعارات لتلقي الأخبار
    - /unsubscribe: إلغاء الاشتراك في الإشعارات
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)

# دالة للاشتراك في الإشعارات
def subscribe(update, context):
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)
    context.bot.send_message(chat_id=chat_id, text="تم الاشتراك في الإشعارات بنجاح.")

# دالة لإلغاء الاشتراك في الإشعارات
def unsubscribe(update, context):
    chat_id = update.effective_chat.id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        context.bot.send_message(chat_id=chat_id, text="تم إلغاء الاشتراك في الإشعارات بنجاح.")
    else:
        context.bot.send_message(chat_id=chat_id, text="أنت غير مشترك في الإشعارات.")

# إعداد وتشغيل البوت
def main():
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
    dp = updater.dispatcher

    # إضافة معالج للأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # إضافة معالج للضغط على الأزرار
    dp.add_handler(CallbackQueryHandler(button))
    
    # إضافة معالج لتفعيل القنوات عند إرسال كلمة "تفعيل"
    dp.add_handler(MessageHandler(Filters.text & Filters.chat_type.channel, activate_channel))

    # إضافة معالج لإظهار الأوامر عند الضغط على الزر
    dp.add_handler(CallbackQueryHandler(show_commands, pattern='show_commands'))

    # إعداد مهمة دورية لإرسال الأخبار كل 20 ثانية
    updater.job_queue.run_repeating(send_news, interval=20, first=0)

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
