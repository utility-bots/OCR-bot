import tesserocr
from PIL import Image
from aiogram import Bot, Dispatcher, types, executor
from config import *
import os
import logging
import psycopg2
import datetime

print(tesserocr.tesseract_version())
print(tesserocr.get_languages())

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)
dir_path = os.path.dirname(os.path.realpath(__file__))
# bot = Bot(token='6257357498:AAH7fl4M6b2BEkKNY47cS1d7h9gpPbiB3Bg')  ## test
bot = Bot(token="6373938814:AAFcxCpoPid-JdogdKcGV-UgWM7fiT7ELkE")

dp = Dispatcher(bot)


class OCRBot:
    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp
        self.user_id = None
        self.text = None
        self.usage = 8
        self.lang = 'fas'
        self.botlang = 'persian'

    def register_handlers(self):
        self.dp.register_message_handler(self.start, commands=["start"])
        self.dp.register_message_handler(self.get_user_images, content_types=types.ContentTypes.PHOTO)
        self.dp.register_message_handler(self.get_user_images_hq, content_types=types.ContentTypes.DOCUMENT)
        self.dp.register_callback_query_handler(self.handle_query)

    async def handle_query(self, query: types.CallbackQuery):
        query_data = query.data
        if query_data == 'remove_backslashn':
            await self.after_processing(query)

        elif query_data == 'persian':
            await self.start_persian(query)

        elif query_data == 'english':
            await self.start_english(query)

        elif query_data == 'charge':
            await self.charge(query)
        elif query_data == 'eng_charge':
            await self.eng_charge(query)

        elif query_data == 'info':
            await self.info(query)
        elif query_data == 'eng_info':
            await self.eng_info(query)

        elif query_data == 'fas' or query_data == 'eng':
            await self.set_lang(query)

    async def set_lang(self, query: types.CallbackQuery):
        await query.answer('زبان عکس دریافتی تنظیم شد')
        self.lang = query.data

    async def charge(self, query: types.CallbackQuery):
        await query.answer()
        charge_text = f'دوست عزیز برای شارژ حساب خود لطفا به @MyTelegramBotsSupport پیام بدید و اطلاعات کاربری خود را بفرستید. هزینه ارتقا استفاده ماهیانه نامحدود 50 هزار تومن است. \n اطلاعات کاربری: {self.user_id} '
        await bot.send_message(chat_id=query.message.chat.id, text=charge_text,
                               parse_mode='markdown', )

    async def eng_charge(self, query: types.CallbackQuery):
        await query.answer()
        #######################add payments
        charge_text = "Dear user, to charge your account, please send a message to @MyTelegramBotsSupport with your user information. The cost for unlimited monthly usage upgrade is 1.5 USD and currently we only support BTC and XMR and other cryptos. \n\nUser information: {}".format(
            self.user_id)
        await bot.send_message(chat_id=query.message.chat.id, text=charge_text,
                               parse_mode='markdown', )

    def connect_db(self):
        conn = psycopg2.connect(
            host=PGHOST,
            database=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD)
        return conn

    def create_table(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS customers
                    (user_id BIGINT NOT NULL UNIQUE,
                    authority BIGINT,
                    ref_id BIGINT,
                    status_pay INT,
                    purchase_time TIMESTAMP,
                    remaining_time TIMESTAMP,
                    usage BIGINT);''')
        conn.commit()
        cursor.close()
        conn.close()

    def insert_initial_data_to_db(self):
        try:
            con = self.connect_db()
            cur = con.cursor()
            cur.execute("""INSERT INTO customers (user_id) VALUES (%s);""", (self.user_id,))

            insert_query = (f'''
            UPDATE customers
            SET usage = 8
            WHERE user_id = %s;
            ''')
            cur.execute(insert_query, (self.user_id,))
            con.commit()
            con.close()
        except Exception as e:
            print(e)
            pass
        finally:
            if con:
                cur.close()
                con.close()

    async def start(self, message: types.Message):
        self.user_id = int(message.chat.id)
        self.insert_initial_data_to_db()
        welcome_message = """
        Welcome to the OCR Master Bot (Image to Text bot) ! Please select bot language.\n
        به بات تبدیل عکس به متن خوش آمدید لطفا زبان بات را انتخاب کنید.
"""
        await message.reply(welcome_message, reply_markup=self.set_bot_lang())

    async def start_persian(self, query: types.CallbackQuery):
        self.botlang = 'persian'
        self.lang = 'fas'
        await query.answer()
        self.user_id = int(query.message.chat.id)
        welcome_message = """
برای بهترین نتیجه از عکس با پشت زمینه سفید و بدون حاشیه استفاده کنید طوری که فقط متن به شکل کاملا خوانا داخل عکس باشد. ربات از پیشرفته ترین api ها بهره میبرد و با قیمتی ارزان در اختیار شما قرار دارد امیدوارم از نتیجه راضی باشید.\n
بات هم از عکس با زبان فارسی هم انگلیسی پشتیبانی میکنید که با دکمه های زیر قابل تغییر است. برای شروع عکس مورد نظر را ارسال کنید.\n
        """
        await bot.send_message(self.user_id, welcome_message,
                               reply_markup=self.get_info_markup())

    async def start_english(self, query: types.CallbackQuery):
        self.botlang = 'english'
        self.lang = 'eng'
        await query.answer()
        self.user_id = int(query.message.chat.id)
        welcome_message = "For the best results, please send images with a white background and clear text. To start, send the image you want to convert.\n"
        await bot.send_message(self.user_id, welcome_message,
                               reply_markup=self.get_eng_info_markup())

    async def get_user_images(self, message: types.Message):
        if self.botlang == 'english':
            await message.reply(text='Processing...')
        else:
            await message.reply(text='در حال پردازش...')

        self.user_id = int(message.chat.id)
        if not (self.check_premium_time() or self.check_free_usage_left()):
            if self.botlang == 'english':
                return await message.reply(text='The bot free usage limit has been reached.',
                                           reply_markup=self.get_eng_charge_markup())
            # if not self.check_free_usage_left():
            return await message.reply(text='تعداد استفاده بات به اتمام رسیده است',
                                       reply_markup=self.get_charge_markup())

        try:
            photo = message.photo[-1]
        except IndexError:
            try:
                photo = message.photo[2]
            except IndexError:
                try:
                    photo = message.photo[1]
                except IndexError:
                    photo = message.photo[0]
        photo_path = await photo.download()

        image = Image.open(photo_path.name)

        PyTess = tesserocr.PyTessBaseAPI(lang=self.lang)
        PyTess.SetImage(image)
        self.text = PyTess.GetUTF8Text()

        # self.text = pytesseract.image_to_string(photo_path.name, lang='eng+fas', )
        os.remove(photo_path.name)

        if self.botlang == 'english':
            await message.reply(text=self.text, reply_markup=self.after_processing_option_eng())
        else:
            await message.reply(text=self.text, reply_markup=self.after_processing_option())

    async def get_user_images_hq(self, message: types.Message):
        if self.botlang == 'english':
            await message.reply(text='Processing...')
        else:
            await message.reply(text='در حال پردازش...')

        self.user_id = int(message.chat.id)

        if not (self.check_premium_time() or self.check_free_usage_left()):
            if self.botlang == 'english':
                return await message.reply(text='The bot free usage limit has been reached.',
                                           reply_markup=self.get_eng_charge_markup())
            # if not self.check_free_usage_left():
            return await message.reply(text='تعداد استفاده بات به اتمام رسیده است',
                                       reply_markup=self.get_charge_markup())

        if message.document.mime_type.split('/')[0] == 'image':
            # await bot.download_file_by_id(key, dir_path + '/UserData/' + user_id + '/' + str(val[user_id]) + '.jpg')
            photo = message.document.file_id

            photo_path = dir_path + '/photos/' + message.document.file_name + '.jpg'
            await bot.download_file_by_id(photo, photo_path)

            image = Image.open(photo_path)

            PyTess = tesserocr.PyTessBaseAPI(lang=self.lang)
            PyTess.SetImage(image)
            self.text = PyTess.GetUTF8Text()

            # self.text = pytesseract.image_to_string(photo_path, lang='eng+fas')
            os.remove(photo_path)
            if self.botlang == 'english':
                await message.reply(text=self.text, reply_markup=self.after_processing_option_eng())
            else:
                await message.reply(text=self.text, reply_markup=self.after_processing_option())

    async def after_processing(self, query: types.CallbackQuery):
        await query.answer()

        text = self.text.replace('\n', ' ')
        await bot.send_message(chat_id=query.message.chat.id, text=text)

    def check_free_usage_left(self):
        con = self.connect_db()
        cur = con.cursor()
        cur.execute("SELECT usage FROM customers WHERE user_id = %s ;", (int(self.user_id),))
        usage = cur.fetchone()[0]

        if usage > 0:
            self.usage = usage - 1
            insert_query = f'''
                UPDATE customers
                SET usage = {self.usage}
                WHERE user_id = {self.user_id};
            '''
            cur.execute(insert_query)

            cur.execute(insert_query)
            con.commit()
            con.close()
            return True

        else:
            return False

    async def info(self, query: types.CallbackQuery):

        await query.answer()
        self.user_id = query.message.chat.id
        con = self.connect_db()
        cur = con.cursor()
        cur.execute('select usage from customers WHERE user_id = %s;',
                    (int(self.user_id),))
        usage = cur.fetchone()[0]

        cur.execute('select purchase_time,remaining_time from customers WHERE user_id = %s;',
                    (int(self.user_id),))
        row = cur.fetchone()

        try:
            purchase_time, remain_time = row
            today = datetime.datetime.today()

            time_left = (remain_time - today).days

            if time_left > 0:
                info_text = ('\nاطلاعات کاربری :'
                             f'\nایدی شما: {self.user_id}'
                             f'\n وضعیت: {str(time_left)} روز استفاده نامحدود باقی مانده است ')
                await bot.send_message(chat_id=query.message.chat.id, text=info_text,
                                       parse_mode='markdown')
            else:
                info_text = ('اطلاعات کاربری :\n'
                             f'ایدی شما:  {self.user_id}\n'
                             f'وضعیت:  {usage} استفاده رایگان\n'
                             )
                await bot.send_message(chat_id=query.message.chat.id, text=info_text,
                                       parse_mode='markdown', reply_markup=self.get_charge_markup())
        except:
            info_text = ('اطلاعات کاربری :\n'
                         f'ایدی شما:  {self.user_id}\n'
                         f'وضعیت:  {usage} استفاده رایگان\n'
                         )
            await bot.send_message(chat_id=query.message.chat.id, text=info_text,
                                   parse_mode='markdown', reply_markup=self.get_charge_markup())

    async def eng_info(self, query: types.CallbackQuery):
        await query.answer()
        self.user_id = query.message.chat.id
        con = self.connect_db()
        cur = con.cursor()
        cur.execute('select usage from customers WHERE user_id = %s;', (int(self.user_id),))
        usage = cur.fetchone()[0]

        cur.execute('select purchase_time,remaining_time from customers WHERE user_id = %s;', (int(self.user_id),))
        row = cur.fetchone()

        try:
            purchase_time, remain_time = row
            today = datetime.datetime.today()

            time_left = (remain_time - today).days
            if time_left > 0:
                info_text = ('\nUser Information:'
                             f'\nYour ID: {self.user_id}'
                             f'\nStatus: {str(time_left)} days of unlimited usage remaining')
                await bot.send_message(chat_id=query.message.chat.id, text=info_text, parse_mode='markdown')
            else:
                info_text = ('User Information:\n'
                             f'Your ID: {self.user_id}\n'
                             f'Status: {usage} free usages remaining')
                await bot.send_message(chat_id=query.message.chat.id, text=info_text, parse_mode='markdown',
                                       reply_markup=self.get_eng_charge_markup())
        except:
            info_text = ('User Information:\n'
                         f'Your ID: {self.user_id}\n'
                         f'Status: {usage} free usages remaining')
            await bot.send_message(chat_id=query.message.chat.id, text=info_text, parse_mode='markdown',
                                   reply_markup=self.get_eng_charge_markup())

    def check_premium_time(self):
        con = self.connect_db()
        cur = con.cursor()

        cur.execute('select purchase_time,remaining_time from customers WHERE user_id = %s;', (int(self.user_id),))
        row = cur.fetchone()
        purchase_time, remain_time = row
        con.close()

        if purchase_time and remain_time:
            current_date = datetime.datetime.today()
            if purchase_time <= current_date <= remain_time:
                return True
            else:
                return False
        return False


    @staticmethod
    def get_info_markup():
        get_info = types.InlineKeyboardMarkup(row_width=2)
        get_info.add(types.InlineKeyboardButton('اطلاعات کاربری', callback_data='info'))
        persian = types.InlineKeyboardButton('عکس به زبان فارسی', callback_data='fas')
        english = types.InlineKeyboardButton('عکس به زبان انگلیسی', callback_data='eng')
        get_info.add(persian, english)
        return get_info

    @staticmethod
    def get_eng_info_markup():
        get_info = types.InlineKeyboardMarkup(row_width=1)
        get_info.add(types.InlineKeyboardButton('User Information', callback_data='eng_info'))
        return get_info

    @staticmethod
    def set_bot_lang():
        get_info = types.InlineKeyboardMarkup(row_width=2)
        persian = types.InlineKeyboardButton('فارسی', callback_data='persian')
        english = types.InlineKeyboardButton('English', callback_data='english')
        get_info.add(persian, english)
        return get_info

    @staticmethod
    def get_charge_markup():
        join_keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
        join_keyboard_markup.add(types.InlineKeyboardButton(
            'شارژ حساب', callback_data='charge'))
        return join_keyboard_markup

    @staticmethod
    def get_eng_charge_markup():
        join_keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
        join_keyboard_markup.add(types.InlineKeyboardButton(
            'Charge Account', callback_data='eng_charge'))
        return join_keyboard_markup

    @staticmethod
    def after_processing_option():
        get_info = types.InlineKeyboardMarkup(row_width=1)
        get_info.add(types.InlineKeyboardButton('حذف فاصله اضافه', callback_data='remove_backslashn'))
        return get_info

    @staticmethod
    def after_processing_option_eng():
        get_info = types.InlineKeyboardMarkup(row_width=1)
        get_info.add(types.InlineKeyboardButton('Remove Extra Spaces', callback_data='remove_backslashn'))
        return get_info

    def run(self):
        self.register_handlers()
        executor.start_polling(dp, skip_updates=True)


ocr_bot = OCRBot(bot, dp)
ocr_bot.run()
