# casio-id-account-generator
Mass account creation with catchall email domains with IMAP for auto otp verification
> The codes support only gmail for imap

## Usage
```sh
python3 main.py
```

## Setup
1. Paste the email and imap password to config file
2. You also need to input your catchall domain.
3. Input the region code for your region. See below on how to get the region code
4. Input the  account password you want for the generated accounts.
> The account generated will look like {random string}@yourcatchalldomain

### Getting the region code
1. Go to https://auth.casio-intl.com/user/registerForm
2. Right click + inspect element
3. Search for `targetCountry`, and input the value next to it in config file
- <img width="379" height="303" alt="image" src="https://github.com/user-attachments/assets/f8ad6a3d-f0c2-4692-9231-5126501c7279" />
4. From this image, input `SGP`

## Preview
<img width="690" height="377" alt="image" src="https://github.com/user-attachments/assets/c8bc48f3-ad7d-49cd-b527-854b0ebead7a" />

## Disclaimer
This project is provided strictly for educational and research purposes only. It is intended to demonstrate programming techniques, web automation, and software development concepts.

By using this project, you agree that you **will not use it** for any illegal, fraudulent, abusive, or unauthorized activities, including but not limited to:
- Creating accounts to violate a website's Terms of Service.
- Circumventing security measures or rate limits.
- Spamming, phishing, or committing fraud.
- Any activity that infringes upon the rights of others.
The author does not encourage, endorse, or assume responsibility for any misuse of this software. Users are solely responsible for ensuring that their use of this project complies with all applicable laws, regulations, and the terms of the websites or services they interact with.
> [!IMPORTANT]  
> If you do not agree with these terms, do not use this project.
