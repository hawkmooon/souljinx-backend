from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, messaging, firestore
import os
import json

app = Flask(__name__)

# Firebase Admin SDK başlat
cred_json = os.environ.get('FIREBASE_CREDENTIALS')
if cred_json:
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate('service-account.json')

firebase_admin.initialize_app(cred)
db = firestore.client()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'app': 'souljinx-backend'})


@app.route('/send-notification', methods=['POST'])
def send_notification():
    data = request.json
    to_uid = data.get('toUid')
    title = data.get('title', 'SoulJinx')
    body = data.get('body', 'Bir şey geldi!')
    effect_type = data.get('effectType', 'vibrationStorm')

    if not to_uid:
        return jsonify({'error': 'toUid gerekli'}), 400

    # Kullanıcının FCM tokenını al
    user_doc = db.collection('users').document(to_uid).get()
    if not user_doc.exists:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    user_data = user_doc.to_dict()
    fcm_token = user_data.get('fcmToken')

    if not fcm_token:
        return jsonify({'error': 'FCM token yok'}), 404

    # Bildirim gönder
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                'effectType': effect_type,
                'click_action': 'FLUTTER_NOTIFICATION_CLICK',
            },
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    priority='max',
                    channel_id='souljinx_effects',
                    sound='default',
                ),
            ),
        )
        response = messaging.send(message)
        return jsonify({'success': True, 'messageId': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/send-effect', methods=['POST'])
def send_effect():
    data = request.json
    from_uid = data.get('fromUid')
    to_uid = data.get('toUid')
    effect_type = data.get('effectType', 'vibrationStorm')

    if not from_uid or not to_uid:
        return jsonify({'error': 'fromUid ve toUid gerekli'}), 400

    # Gönderen istatistiğini güncelle
    db.collection('users').document(from_uid).update({
        'totalSent': firestore.Increment(1),
    })

    # Bildirim gönder
    effect_names = {
        'vibrationStorm': '💥 Titreşim Kasırgası',
        'screenCrack': '💔 Ekran Çatlıyor',
        'eyesRain': '👁️ Gözler',
        'timerPressure': '⏱️ Zamanlayıcı',
        'matrixRain': '🌧️ Ekran Yağmuru',
        'voodooNeedle': '🪆 Voodoo İğnesi',
        'deleteThreat': '🗑️ Silme Tehdidi',
        'timeStop': '🕰️ Zaman Durdu',
        'morseLove': '💌 Morse Titreşim',
        'waitingPenalty': '😤 Bekleme Cezası',
        'luckyCard': '🎴 Şans Kartı',
        'emotionTest': '🎭 Duygu Testi',
        'nightMode': '🌙 Gece Modu',
        'screenLock': '🔒 Ekran Hapsi',
    }

    effect_name = effect_names.get(effect_type, 'Bir efekt')

    user_doc = db.collection('users').document(to_uid).get()
    if not user_doc.exists:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    user_data = user_doc.to_dict()
    fcm_token = user_data.get('fcmToken')

    if fcm_token:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title='SoulJinx 💜',
                    body=f'{effect_name} geliyor!',
                ),
                data={
                    'effectType': effect_type,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        priority='max',
                        channel_id='souljinx_effects',
                        sound='default',
                    ),
                ),
            )
            messaging.send(message)
        except Exception as e:
            print(f'FCM hatası: {e}')

    return jsonify({'success': True})


@app.route('/send-message-notification', methods=['POST'])
def send_message_notification():
    data = request.json
    to_uid = data.get('toUid')
    sender_name = data.get('senderName', 'Eşin')
    message_text = data.get('messageText', 'Yeni mesaj')

    if not to_uid:
        return jsonify({'error': 'toUid gerekli'}), 400

    user_doc = db.collection('users').document(to_uid).get()
    if not user_doc.exists:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    user_data = user_doc.to_dict()
    fcm_token = user_data.get('fcmToken')

    if not fcm_token:
        return jsonify({'error': 'FCM token yok'}), 404

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=f'💜 {sender_name}',
                body=message_text,
            ),
            data={
                'type': 'message',
                'click_action': 'FLUTTER_NOTIFICATION_CLICK',
            },
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    priority='max',
                    channel_id='souljinx_messages',
                    sound='default',
                ),
            ),
        )
        response = messaging.send(message)
        return jsonify({'success': True, 'messageId': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)