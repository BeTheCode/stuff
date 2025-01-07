# app.py
from aws_cdk import App
from stacks.iot_stack import IoTMLStack

app = App()
IoTMLStack(app, "IoTMLStack")
app.synth()