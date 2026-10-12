import json
import os
import requests
import boto3

def lambda_handler(event, context):
    city = os.environ.get('CITY', 'Jhansi')
    api_key = os.environ['OPENWEATHER_API_KEY']
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    response = requests.get(url)
    data = response.json()

    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed'] * 3.6  # m/s → km/h
    condition = data['weather'][0]['description'].lower()

    sns = boto3.client('sns')
    alerts = []

    # Temperature Alerts
    if temp > 38:
        alerts.append(f"🔥 Extreme Heat Alert! It's {temp}°C in {city}. Avoid going outside.")
    elif 35 < temp <= 38:
        alerts.append(f"🥵 High Temperature Alert! It's {temp}°C. Stay hydrated!")
    elif temp < 5:
        alerts.append(f"❄️ Extreme Cold Alert! It's {temp}°C in {city}. Bundle up!")
    elif 5 <= temp < 10:
        alerts.append(f"🥶 Cold Weather Alert! It's {temp}°C in {city}. Dress warmly!")

    # Humidity Alerts
    if humidity > 85:
        alerts.append(f"💧 High Humidity Alert! Humidity is {humidity}% — air feels heavy.")
    elif humidity < 25:
        alerts.append(f"🌵 Low Humidity Alert! Humidity is {humidity}%. Skin may feel dry.")

    # Wind Alerts
    if wind_speed > 40:
        alerts.append(f"🌪️ Strong Wind Alert! Wind speed is {wind_speed:.1f} km/h. Secure loose objects.")
    elif 25 < wind_speed <= 40:
        alerts.append(f"💨 Windy Conditions! Wind speed: {wind_speed:.1f} km/h.")

    # Condition Alerts
    if "rain" in condition:
        alerts.append(f"🌧️ Rain Alert! {condition.title()} in {city}. Carry an umbrella.")
    elif "drizzle" in condition:
        alerts.append(f"☔ Drizzle Alert! Light rain expected in {city}.")
    elif "thunder" in condition or "storm" in condition:
        alerts.append(f"⛈️ Storm Alert! {condition.title()} in {city}. Stay indoors.")
    elif "snow" in condition:
        alerts.append(f"❄️ Snow Alert! {condition.title()} in {city}. Roads may be slippery.")
    elif "fog" in condition or "mist" in condition or "haze" in condition or "smoke" in condition:
        alerts.append(f"🌫️ Low Visibility Alert! {condition.title()} in {city}. Drive carefully.")
    elif "clear" in condition:
        alerts.append(f"☀️ Clear Sky! Enjoy the good weather in {city}.")
    elif "cloud" in condition:
        alerts.append(f"☁️ Cloudy Skies! Expect mild conditions in {city}.")

    # Summary
    summary = (
        f"📍 Weather Summary for {city}\n"
        f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)\n"
        f"💧 Humidity: {humidity}%\n"
        f"🌬️ Wind Speed: {wind_speed:.1f} km/h\n"
        f"🌤️ Condition: {condition.title()}"
    )

    if alerts:
        message = summary + "\n\n🚨 Alerts:\n" + "\n".join(alerts)
        subject = f"⚠️ Weather Alert for {city}"
    else:
        message = summary + "\n\n✅ No severe weather conditions detected."
        subject = f"✅ Weather Update for {city}"

    sns.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)
    print("Notification sent successfully!")

    return {'statusCode': 200, 'body': json.dumps('Weather check completed successfully!')}
