import RPi.GPIO as GPIO
import board
import busio
from adafruit_pca9685 import PCA9685
import time

# --- Setup I2C et PCA9685 ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# --- Setup GPIO pour la direction ---
GPIO.setmode(GPIO.BCM)

IN1 = 23 # Direction Moteur 1
IN2 = 18  # Direction Moteur 1
IN3 = 27  # Direction Moteur 2
IN4 = 22  # Direction Moteur 2

for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)

# Canaux PCA9685 pour le PWM
# A5 = canal 5, A4 = canal 4 (à vérifier)
CANAL_MOTEUR1 = 5  # A5
CANAL_MOTEUR2 = 4  # A4

def set_vitesse(canal, vitesse_pct):
    """Vitesse en % (0-100) → valeur PCA9685 (0-65535)"""
    valeur = int((vitesse_pct / 100) * 65535)
    pca.channels[canal].duty_cycle = valeur

def avancer_progressif(vitesse_cible=40, duree=2):
    print("Avance progressivement...")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)

    for vitesse in range(30, vitesse_cible + 1, 2):
        set_vitesse(CANAL_MOTEUR1, vitesse)
        set_vitesse(CANAL_MOTEUR2, vitesse)
        print(f"Vitesse : {vitesse}%")
        time.sleep(0.1)

    time.sleep(duree)

def reculer_progressif(vitesse_cible=40, duree=2):
    print("Recule progressivement...")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)

    for vitesse in range(30, vitesse_cible + 1, 2):
        set_vitesse(CANAL_MOTEUR1, vitesse)
        set_vitesse(CANAL_MOTEUR2, vitesse)
        print(f"Vitesse : {vitesse}%")
        time.sleep(0.1)

    time.sleep(duree)

def arreter():
    set_vitesse(CANAL_MOTEUR1, 0)
    set_vitesse(CANAL_MOTEUR2, 0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    print("Arrêt")

try:
    avancer_progressif(vitesse_cible=40, duree=2)
    arreter()
    time.sleep(1)

    reculer_progressif(vitesse_cible=40, duree=2)
    arreter()

except KeyboardInterrupt:
    print("Arrêt d'urgence")

finally:
    arreter()
    pca.deinit()
    GPIO.cleanup()