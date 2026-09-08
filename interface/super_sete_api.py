"""Wrapper de interface REST para Motor Super Sete B2B."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from motor_supersete import MotorSuperSeteB2B

def instanciar_motor(**kwargs):
    return MotorSuperSeteB2B(**kwargs)
