from django.shortcuts import render,redirect
from scraping.ticket import search_city
from django.http import FileResponse, HttpResponseNotFound
from .forms import CustomUserCreationForm
from django.contrib.auth import login as auth_login
import os
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required

def download_file(request):
    file_path = os.path.join('C:/Users/irani/apartment_scraping', 'output.xlsx')  # Update this path if necessary
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='output.xlsx')
    else:
        return HttpResponseNotFound("File not found.")





def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            auth_login(request, user)
            return redirect('home')  # Redirect to the home page after successful registration
    else:
        form = CustomUserCreationForm()
    return render(request, 'scraping/signup.html', {'form': form})




def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                auth_login(request, user)
                return redirect('home')  # Redirect to the home page after successful login
        else:
            return redirect('signup')  # Redirect to the signup page if credentials are not valid
    else:
        form = AuthenticationForm()
    return render(request, 'scraping/login.html', {'form': form})



def search(request):
    if request.method == "POST":
        city = request.POST.get('city')
        country = request.POST.get('country')  # Make sure the form includes a 'country' field
        
        if country=="USA":
            # Call the search_city function and get the results
            zumper_data, apartments_data = search_city(city, country)
            prices_zumper, addresses_zumper, phones_zumper = zumper_data
            price_apartments, beds_apartments, phones_apartments, addresses_apartments = apartments_data
            
            # Since Zumper does not have bed information, create a list of "Not Available"
            beds_zumper = ["Not Available"] * len(prices_zumper)
            
            # Combine the results for display
            combined_prices = prices_zumper + price_apartments
            combined_beds = beds_zumper + beds_apartments
            combined_phones = phones_zumper + phones_apartments
            combined_addresses = addresses_zumper + addresses_apartments
            
            # Pair the results together
            results = zip(combined_prices, combined_beds, combined_phones, combined_addresses)
            
            # Pass the results to the template
            context = {
                'results': results,
                'city': city,
                'country': country,
            }
            return render(request, 'scraping/home.html', context)
        elif country=="Canada":
            zumper_data, apartments_data, data_rentseekers= search_city(city, country)
            prices_zumper, addresses_zumper, phones_zumper = zumper_data
            price_apartments, beds_apartments, phones_apartments, addresses_apartments = apartments_data
            prices_seeker, addresses_seeker, phone_seekers = data_rentseekers
            
            # Since Zumper does not have bed information, create a list of "Not Available"
            beds_zumper = ["Not Available"] * len(prices_zumper)
            beds_seeker = ["Not Available"] * len(prices_seeker)
            
            # Combine the results for display
            combined_prices = prices_zumper + price_apartments + prices_seeker
            combined_beds = beds_zumper + beds_apartments 
            combined_phones = phones_zumper + phones_apartments + phone_seekers
            combined_addresses = addresses_zumper + addresses_apartments+addresses_seeker
            
            # Pair the results together
            results = zip(combined_prices, combined_beds, combined_phones, combined_addresses)
            
            # Pass the results to the template
            context = {
                'results': results,
                'city': city,
                'country': country,
            }
            return render(request, 'scraping/home.html', context)

    return render(request, 'scraping/home.html')


def terms(request):
    return render(request, 'scraping/terms.html')


@login_required
def user_profile(request):
    # Access user information
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'scraping/user_profile.html', context)
 