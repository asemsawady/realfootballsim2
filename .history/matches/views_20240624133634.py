from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView
from .models import Match
from .match_simulation import simulate_match

class CreateMatchView(CreateView):
    model = Match
    fields = ['home_team', 'away_team', 'date']
    template_name = 'matches/create_match.html'

    def form_valid(self, form):
        match = form.save()
        return redirect('match_detail', pk=match.pk)

class MatchDetailView(DetailView):
    model = Match
    template_name = 'matches/match_detail.html'

def simulate_match_view(request, match_id):
    simulate_match(match_id)
    return redirect('match_detail', pk=match_id)
