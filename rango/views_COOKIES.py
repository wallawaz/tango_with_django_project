from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime

def encode_url(str):
    return str.replace(' ', '_')

def decode_url(str):
    return str.replace('_', ' ')


def index(request):
	# Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    request.session.set_test_cookie()
    context = RequestContext(request)
    
    # Query the DB for a list of ALL categories currently stored .
    # Order the categories by number of likes in desc order.
    # Retrieve the top 5 only - or all if < 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = { 'categories' : category_list, 'pages': page_list }

    # Loop thru each category returned, and create a URL attribute.
    # This attribute stores an encoded URL (e.g. spaces replaced w/ underscores).
    for category in category_list:
        category.url = encode_url(category.name)

	# Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.

    # # # # COOKIES...
    # Obtain response early so we can add cookie info to it ...
    response = render_to_response('rango/index.html', context_dict, context)   

    # Get the number of visits to the site.
    # We use COOKIES.get() to obtain the visits cookie.
    # If cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, we default to zero and cast that.
    visits = int( request.COOKIES.get('visits', '0'))

    # Does the cookie last_visit exist yet?
    if request.COOKIES.has_key('last_visit'):    
        # Yes it does, get the cookie's value:
        last_visit = request.COOKIES['last_visit']
        # Cast the value to a Python date/time object.
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        # If its been > a day since the last visit . . .
        if ( datetime.now() - last_visit_time ).seconds > 5:
            # reassign the value of cookie to +1 of that which it was before.
            response.set_cookie('visits', visits+1)
            # and update the last_visit cookie, too.
            response.set_cookie('last_visit', datetime.now())
    else:
        # Cookie last_visit doesn't exist, so create it in current date/time.
        response.set_cookie('last_visit', datetime.now())

    # Return response back to user, updating any cookies that need changed.
    return response 


def about(request):
    context = RequestContext(request)
    return render_to_response('rango/about.html', {}, context)
	#return HttpResponse("Rango says here is the about Page. <a href='/rango/'>Index </a>")

def category(request, category_name_url):
    # Request the context of the request.
    context = RequestContext(request)
    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    category_name = decode_url(category_name_url)
    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name': category_name, 'category_name_url' : category_name_url}
    
    # Can we find a category with the given name?
    # If we can't, the .get() method raises a DoesNotExist exception.
    # So the .get() method returns one model instance or raises an exception.        
    try:
        category = Category.objects.get(name=category_name)
        print '******', category_name,  '******'
        # retrieve all assoc. pages.
        # Filter wll return >= 1 model instance
        pages = Page.objects.filter(category=category)

        # Add our results list to the template context under name pages:
        context_dict['pages'] = pages

        # We also add the category object from the database to the context dictonary.
        # We will use this in the template to verify that the category exists. 
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didnt find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
    return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)

    # A HTTP POST ?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            # Save the new category to the DB.
            form.save(commit=True)

            # Now call the index() view.
            # THe user will be shown the homepage.
            return index(request)  
        else:
            # The supplied form contained errors - just print them to terminal.
            print form.errors
    else:
        # if the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', {'form' : form}, context) 

@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            # This time we cannot commit right away.
            # Not all fields are auto populated!
            page = form.save(commit=False)

            # Retrieve the assoc Category object so we can add it.
            # Wrap the code in a try block - check if the category actually exists ! 
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                # If we get here then the Category does not exist.
                # Go back and render the add category form as a way of saying the category does not exist.
                return render_to_response('rango/add_category.html', {}, context)

            # Create default # of page views.
            page.views=0

            # With this we can now save our new model instance.
            page.save()

            # Now that the page is saved, display the category listed.
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()
    return render_to_response('rango/add_page.html',
        {'category_name_url': category_name_url,
        'category_name' : category_name,
        'form' : form }, 
        context)

# # USER FORMS # # # # # 
def register(request):
    # Like before, get the request's context.
    if request.session.test_cookie_worked():
        print ">>>> TEST COOKIE WORKED!"
        request.session.delete_test_cookie()
    context = RequestContext(request)

    # A boolean value for telling the template whether  the registration was successful .
    # Set to false initally. Code changes value to True when registrarion succeeds.
    registered=False

    # If it's a HTTP POST, we're interested in processing the form data.
    if request.method == 'POST':
        # Attempt to grab info from the raw form information now.
        # Note that we make use of both UserForm & UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid . . . 
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to db.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now we sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we are ready to avoid integrity problems...
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile pic?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile_picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form(s) - mistakes or something else ?
        # Print problems to terminal.
        # They will also be shown later.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we will render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response(
        'rango/register.html'
        , {'user_form': user_form, 'profile_form': profile_form, 'registered' : registered}
        , context
        )

def user_login(request):
    # Like before, get the request's context.
    context = RequestContext(request)
    if request.method == 'POST':
        # If request is a POST, try to pull relevant info.
        # Gather user and password provided
        # obtained from login form.
        username = request.POST['username']
        password = request.POST['password']
        print "We hit the page", username, login

        # Use Django's machinery to attempt to see if the username/password comb. is valid.
        # A User Object is returned if it is...
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absenece of value), no user with matching credentials 
        # was found.
        if user is not None:
            # Is the account active? It could have been disabled ...
            if user.is_active:
                # If account is valid & active, we can log user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # Inactive account used, dont login.
                return HttpResponse("Your rango account was deactivated.")
        else:
            # Bad login details. So we can't login.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likley be a HTTP GET.           
    else:
        # No context variables to pass to the template system, hence the 
        # blank dict obj.
        return render_to_response('rango/login.html', {}, context)

@login_required
def restricted(request):
    context = RequestContext(request)
    return render_to_response('rango/restricted.html', {}, context)
    

@login_required
def user_logout(request):
    # Since we already know they are logged in , we can now just log them out.
    logout(request)

    # Take back to the homepage.
    return HttpResponseRedirect('/rango/')