from django import forms
from rango.models import Page, Category, UserProfile
from django.contrib.auth.models import User

class CategoryForm(forms.ModelForm):
	name = forms.CharField(max_length=128, help_text="Please Enter the Category Name.")
	views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
	likes = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
	
	# An inline class to provide additional info on the form.
	class Meta:
		# Provide an association between the ModelForm and the model
		model = Category

class PageForm(forms.ModelForm):
	title = forms.CharField(max_length=128, help_text="Please enter the title of the Page.")
	url = forms.URLField(max_length=200, help_text="Please enter the URL of the page.")
	views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

	def clean(self):
		cleaned_data = self.cleaned_data
		url = cleaned_data.get('url')

		# If url is not empty and doesnt start with "http://", preappend "http://".
		if url and not url.startswith('http://'):
			url = 'http://' + url
			cleaned_data['url'] = url

		return cleaned_data

	class Meta:
		# Provide association between the ModelForm and the model.
		model = Page
		# What fields do we want to include in our form?
        # This way we don't need every field in the model present.
        # Some fields may allow NULL values, so we may not want to include them...
        # Here, we are hiding the foreign key.
        field = ('title', 'url', 'views')

class UserForm(forms.ModelForm):
	username = forms.CharField(help_text="Please enter your username")
	email = forms.CharField(help_text="Please enter your email")
	password = forms.CharField(widget=forms.PasswordInput(), help_text="Please Enter a password")

	class Meta:
		model = User
		fields = ['username','password','email']

class UserProfileForm(forms.ModelForm):
	website = forms.URLField(help_text="Please enter your website.", required=False)
	picture = forms.ImageField(help_text="Select a profile image to upload.", required=False)
	
	class Meta:
		model = UserProfile
		fields =['website', 'picture']
