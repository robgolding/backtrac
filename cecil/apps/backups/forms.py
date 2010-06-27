from django import forms

from models import Backup

class BackupForm(forms.ModelForm):
	
	class Meta:
		model = Backup
