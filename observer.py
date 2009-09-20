class Observer:
	
	def __init__(self, caller):
		self.caller = caller
		caller.addView(self)
	
	def update(self, msg):
		pass