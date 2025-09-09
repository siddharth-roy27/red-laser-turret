import RPi.GPIO as GPIO
import time

class TurretController:
    def __init__(self, cfg):
        self.cfg = cfg
        h = cfg["hardware"]
        self.servo_x_pin = h["servo_x_pin"]
        self.servo_y_pin = h["servo_y_pin"]
        self.button_pin  = h["button_pin"]
        self.pwm_hz      = h["pwm_hz"]
        self.min_us      = h["pulse_min_us"]
        self.max_us      = h["pulse_max_us"]

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_x_pin, GPIO.OUT)
        GPIO.setup(self.servo_y_pin, GPIO.OUT)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.pwm_x = GPIO.PWM(self.servo_x_pin, self.pwm_hz)
        self.pwm_y = GPIO.PWM(self.servo_y_pin, self.pwm_hz)
        self.pwm_x.start(0)
        self.pwm_y.start(0)

        c = cfg["control"]
        self.ang_x = 90.0
        self.ang_y = 90.0
        self.ang_min = c["limit_deg_min"]
        self.ang_max = c["limit_deg_max"]
        self.max_step = c["max_step_deg"]

        self._write_angles()

    def _angle_to_duty(self, angle_deg):
        # map angle to duty cycle: use pulse width within [min_us, max_us]
        pw = self.min_us + (self.max_us - self.min_us) * (angle_deg / 180.0)
        period_us = 1_000_000.0 / self.pwm_hz
        duty = 100.0 * (pw / period_us)
        return max(0.0, min(100.0, duty))

    def _write_angles(self):
        dx = self._angle_to_duty(self.ang_x)
        dy = self._angle_to_duty(self.ang_y)
        self.pwm_x.ChangeDutyCycle(dx)
        self.pwm_y.ChangeDutyCycle(dy)
        time.sleep(0.02)

    def nudge(self, d_ang_x, d_ang_y):
        # slew-limit
        d_ang_x = max(-self.max_step, min(self.max_step, d_ang_x))
        d_ang_y = max(-self.max_step, min(self.max_step, d_ang_y))
        self.ang_x = max(self.ang_min, min(self.ang_max, self.ang_x + d_ang_x))
        self.ang_y = max(self.ang_min, min(self.ang_max, self.ang_y + d_ang_y))
        self._write_angles()

    def button_pressed(self):
        # Active LOW
        return GPIO.input(self.button_pin) == GPIO.LOW

    def close(self):
        try:
            self.pwm_x.stop()
            self.pwm_y.stop()
        finally:
            GPIO.cleanup()
