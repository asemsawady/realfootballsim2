from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Championship, Season, League
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
import json
from django.utils import timezone
from django.http import JsonResponse
from django.db import models

class ChampionshipListView(LoginRequiredMixin, ListView):
    model = Championship
    template_name = 'tournaments/championship_list.html'
    context_object_name = 'championships'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_seasons'] = Season.objects.filter(is_active=True)
        # Убираем country из select_related
        context['championships'] = Championship.objects.all().select_related(
            'league', 'season'
        ).order_by('league__level')
        return context

class ChampionshipDetailView(LoginRequiredMixin, DetailView):
    model = Championship
    template_name = 'tournaments/championship_detail.html'
    context_object_name = 'championship'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Изменяем название аннотации на goals_diff
        context['standings'] = (
            self.object.championshipteam_set
            .annotate(
                goals_diff=models.F('goals_for') - models.F('goals_against')
            )
            .order_by('-points', '-goals_diff', '-goals_for')
        )
        
        matches = self.object.championshipmatch_set.all().select_related(
            'match', 
            'match__home_team', 
            'match__away_team'
        ).order_by('round', 'match__date')
        
        context['matches'] = matches
        
        calendar_events = []
        for match in matches:
            calendar_events.append({
                'id': match.id,
                'title': f"{match.match.home_team} vs {match.match.away_team}",
                'start': match.match.date.isoformat(),
                'status': match.match.status,
                'score': f"{match.match.home_score} - {match.match.away_score}" if match.match.status == 'finished' else None,
                'url': reverse('matches:match_detail', args=[match.match.id]),
                'className': f"match-{match.match.status}"
            })
        
        context['calendar_events'] = json.dumps(calendar_events)
        context['user_timezone'] = self.request.session.get('timezone', timezone.get_current_timezone_name())
        
        return context

class ChampionshipCalendarView(LoginRequiredMixin, DetailView):
    model = Championship
    template_name = 'tournaments/championship_calendar.html'
    context_object_name = 'championship'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class SeasonListView(LoginRequiredMixin, ListView):
    model = Season
    template_name = 'tournaments/season_list.html'
    context_object_name = 'seasons'

class LeagueListView(LoginRequiredMixin, ListView):
    model = League
    template_name = 'tournaments/league_list.html'
    context_object_name = 'leagues'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Группируем лиги по странам и уровням
        countries = {}
        for league in self.get_queryset().order_by('country', 'level'):
            if league.country not in countries:
                countries[league.country] = []
            countries[league.country].append(league)
        context['countries'] = countries
        return context
def set_timezone(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST.get('next', '/'))
    else:
        return redirect('/')

def get_championship_matches(request, pk):
    championship = Championship.objects.get(pk=pk)
    matches = championship.championshipmatch_set.all().select_related(
        'match', 
        'match__home_team', 
        'match__away_team'
    )
    
    match_data = [{
        'id': match.id,
        'round': match.round,
        'date': match.match.date.isoformat(),
        'home_team': match.match.home_team.name,
        'away_team': match.match.away_team.name,
        'status': match.match.status,
        'score': f"{match.match.home_score}-{match.match.away_score}" if match.match.status == 'finished' else None
    } for match in matches]
    
    return JsonResponse({'matches': match_data})