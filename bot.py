import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler

# --- CONFIGURACIÓN ---
TOKEN = "8686427863:AAEV9KfOB5kpfo2FK9WFerocC3Y3XF3MiHw"
MI_ID_TELEGRAM = 8595668429
PORT = int(os.environ.get('PORT', 8080))

# 1. ENGAÑO PARA RENDER: Servidor web mínimo
class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SERVIDOR ACTIVO")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), WebHandler)
    server.serve_forever()

# 2. LÓGICA DEL BOT
DATOS, RUTA, FECHA = range(3)
logging.basicConfig(level=logging.INFO)

async def post_init(app: Application):
    await app.bot.set_my_commands([BotCommand("start", "Menú Principal")])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "⭐ **VIAJANDO CUBA GESTIÓN** ⭐\n\n"
        "Somos tu mejor opción para asegurar tu pasaje con rapidez y seguridad.\n"
        "📍 _Complete los pasos en orden:_ "
    )
    btns = [
        [InlineKeyboardButton("📝 Registrar Identidad", callback_data='d')],
        [InlineKeyboardButton("📍 Definir Provincias", callback_data='r')],
        [InlineKeyboardButton("📅 Tiempo de Antelación", callback_data='f')],
        [InlineKeyboardButton("🚀 ENVIAR SOLICITUD", callback_data='e')]
    ]
    markup = InlineKeyboardMarkup(btns)
    if update.message: await update.message.reply_text(texto, reply_markup=markup, parse_mode='Markdown')
    else: await update.callback_query.message.edit_text(texto, reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data == 'd': 
        await q.message.reply_text("👤 Escriba **Nombre y Carnet**:")
        return DATOS
    if q.data == 'r':
        await q.message.reply_text("🗺️ Escriba **Provincia Origen y Destino**:")
        return RUTA
    if q.data == 'f':
        btns = [[InlineKeyboardButton("⏳ 72 Horas", callback_data='f72')], [InlineKeyboardButton("📅 1 Mes", callback_data='f1m')]]
        await q.message.reply_text("⏰ Antelación:", reply_markup=InlineKeyboardMarkup(btns))
        return FECHA
    if q.data == 'e':
        d = context.user_data
        if all(k in d for k in ('id', 'ru', 'ti')):
            res = f"🚨 **NUEVO PEDIDO**\n👤 {d['id']}\n📍 {d['ru']}\n⏰ {d['ti']}"
            await context.bot.send_message(chat_id=MI_ID_TELEGRAM, text=res)
            await q.message.reply_text("✅ **¡Enviado!** Contactaremos con usted.")
        else: await q.message.reply_text("⚠️ Faltan datos.")
        return await start(update, context)

async def h_id(u, c): c.user_data['id'] = u.message.text; return await start(u, c)
async def h_ru(u, c): c.user_data['ru'] = u.message.text; return await start(u, c)
async def h_fe(u, c):
    q = u.callback_query; await q.answer()
    c.user_data['ti'] = "72h" if q.data == 'f72' else "1 Mes"
    return await start(u, c)

def main():
    # Iniciamos el "engaño" web en un hilo separado
    threading.Thread(target=run_web_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(botones)],
        states={
            DATOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_id)],
            RUTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_ru)],
            FECHA: [CallbackQueryHandler(h_fe, pattern='^f')],
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    app.add_handler(conv)
    print("Bot en ejecución...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
