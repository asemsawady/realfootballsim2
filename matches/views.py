from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q
from .models import Match, MatchEvent
from clubs.models import Club

class CreateMatchView(CreateView):
    model = Match
    fields = ['home_team', 'away_team', 'datetime']
    template_name = 'matches/create_match.html'

    def form_valid(self, form):
        match = form.save()
        return redirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))

class MatchDetailView(LoginRequiredMixin, DetailView):
    model = Match
    template_name = 'matches/match_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match_events'] = self.object.events.order_by('minute')
        context['is_user_team'] = (
            self.request.user.club == self.object.home_team or 
            self.request.user.club == self.object.away_team
        )
        return context

class MatchListView(LoginRequiredMixin, ListView):
    model = Match
    template_name = 'matches/match_list.html'
    context_object_name = 'matches'

    def get_queryset(self):
        championship_id = self.kwargs.get('championship_id')
        if championship_id:
            return Match.objects.filter(
                championshipmatch__championship_id=championship_id
            ).order_by('championshipmatch__round', 'datetime')
        # Если нет championship_id, показываем матчи команды пользователя
        return Match.objects.filter(
            Q(home_team=self.request.user.club) | 
            Q(away_team=self.request.user.club)
        )

@login_required
def get_match_events(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    events = match.events.order_by('minute').values('minute', 'event_type', 'description')
    return JsonResponse({
        'events': list(events), 
        'match': {
            'home_team': match.home_team.name,
            'away_team': match.away_team.name,
            'final_score': {
                'home': match.home_score,
                'away': match.away_score
            }
        }
    })

@login_required
def simulate_match_view(request, match_id):
    # Если match_id = 0, создаем новый тестовый матч
    if match_id == 0:
        # Получаем клуб пользователя
        club = request.user.club
        # Выбираем случайного бота-соперника
        opponent = Club.objects.filter(is_bot=True).exclude(id=club.id).order_by('?').first()
        if not opponent:
            return render(request, 'matches/no_opponent.html', {'club': club})
        
        # Создаем новый матч и сразу ставим его in_progress
        match = Match.objects.create(
            home_team=club,
            away_team=opponent,
            datetime=timezone.now(),
            status='in_progress',
            current_minute=0
        )
        match_id = match.id
    
    # Редирект на страницу матча
    return redirect('matches:match_detail', pk=match_id)
