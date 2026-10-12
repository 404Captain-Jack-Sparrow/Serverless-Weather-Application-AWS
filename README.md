# 🌦️ AWS Weather Alert System using Lambda, SNS, and EventBridge

This project automatically checks the current weather conditions (temperature, humidity, wind speed, and sky condition) for a specific city using the **OpenWeatherMap API**, analyzes the data, and sends weather alerts via **Amazon SNS** (email or SMS).

It runs automatically at scheduled intervals using **Amazon EventBridge**.

---

## 📌 Project Overview

### How it works

1. **EventBridge Rule (Scheduler)** triggers the AWS Lambda function at a fixed interval (for example, every 3 hours).
2. **Lambda** calls the OpenWeatherMap API to get the latest weather data for your chosen city (e.g., Jhansi).
3. The Lambda function analyzes the data:
   - Checks temperature (hot / cold)
   - Checks humidity (high / low)
   - Checks wind speed (windy / storm)
   - Checks weather condition (rain, snow, fog, etc.)
4. Based on the results, it prepares a **summary + alerts** message.
5. The message is published to an **SNS Topic**, which notifies users via Email or SMS.

---

## ☁️ AWS Services Used

| Service | Purpose |
|---|---|
| **AWS Lambda** | Executes the Python script that fetches and processes weather data |
| **Amazon SNS** | Sends alerts to users via email or SMS |
| **Amazon EventBridge** | Triggers Lambda automatically at scheduled intervals |
| **OpenWeatherMap API** | Provides real-time weather data |

---

## ⚙️ Lambda Function Workflow

1. Fetch weather data using the OpenWeatherMap API
2. Extract temperature, humidity, wind speed, and conditions
3. Analyze values to detect:
   - 🔥 Extreme heat
   - ❄️ Cold weather
   - 🌪️ Strong winds
   - 🌧️ Rain / storm / fog
4. Combine everything into a detailed report
5. Send results to SNS for user notification

---

## 🔐 Environment Variables in Lambda

Set these in **Lambda → Configuration → Environment variables**:

| Variable Name | Description | Example |
|---|---|---|
| `OPENWEATHER_API_KEY` | Your API key from OpenWeatherMap | `YOUR_WEATHER_API` |
| `SNS_TOPIC_ARN` | The ARN of your SNS topic | `YOUR_SNS_ARN` |
| `CITY` *(optional)* | City to monitor (defaults to Jhansi) | `Jhansi` |

> ⚠️ **Never commit your real API key to GitHub.** Keep it only in Lambda environment variables.

---

## 🚀 Setup Guide

### Step 1: Create the SNS Topic and Subscription

1. Go to **Amazon SNS → Topics → Create topic**
2. Type: **Standard**
3. Name: `lambdaTopic`
4. Click **Create subscription**
   - Protocol: **Email**
   - Endpoint: your email address
5. Confirm the subscription by clicking the link in the email you receive.

![Create SNS subscription](screenshots/01-sns-create-subscription.png)

After confirming, the subscription status shows **Confirmed**:

![SNS subscription confirmed](screenshots/05-sns-subscription-confirmed.png)

---

### Step 2: Create the Lambda Function

1. Go to **Lambda → Functions → Create function → Author from scratch**
2. Function name: `WeatherAlertFunction`
3. Runtime: **Python 3.x**
4. Under **Additional configurations**, enable **Custom execution role** and create/select a role.

![Lambda execution role](screenshots/02-lambda-execution-role.png)

5. Click **Create function**.

![Lambda function created](screenshots/03-lambda-function-created.png)

6. Add the permission to publish to SNS. Attach an inline policy to the execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "YOUR_SNS_TOPIC_ARN"
    }
  ]
}
```

7. Paste the code below into `lambda_function.py` and click **Deploy**.

---

### Lambda Function Code (Python)

```python
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
```

> 💡 The `requests` library is not included in the default Lambda runtime. If you get an `ImportModuleError`, add it through a Lambda Layer or switch to Python's built-in `urllib.request`.

---

### Step 3: Create the EventBridge Rule (Scheduler)

1. Go to **EventBridge → Rules → Create rule**
2. Choose **Schedule**
3. Set your schedule, for example:
   - `rate(3 hours)` — every 3 hours
   - `cron(0 8 * * ? *)` — every day at 8 AM UTC
4. Under **Target**, choose **AWS service → Lambda function**, then select `WeatherAlertFunction`.
5. Create the rule.

---

### Step 4: Test the Lambda Function

1. Open your Lambda function and go to the **Test** tab.
2. Click **Configure test event → Create new event** (the default empty `{}` event works).
3. Click **Test**.
4. Check your email for the SNS notification.

![Lambda test succeeded](screenshots/04-lambda-test-success.png)

---

## 📧 Example Output (Email)

```
📍 Weather Summary for Jhansi
🌡️ Temperature: 30°C (Feels like 32°C)
💧 Humidity: 70%
🌬️ Wind Speed: 12.6 km/h
🌤️ Condition: Light Rain

🚨 Alerts:
🌧️ Rain Alert! Light Rain in Jhansi. Carry an umbrella.
```

---

## 🔮 Future Improvements

- Support multiple cities at once
- Add weather trend analysis (day-to-day comparison)
- Store logs in DynamoDB

---

## 🙏 Acknowledgements

- AWS Lambda, SNS, and EventBridge for automation
- OpenWeatherMap for the free weather data API
