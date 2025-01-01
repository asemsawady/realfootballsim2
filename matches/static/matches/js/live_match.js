document.addEventListener('DOMContentLoaded', function() {
    const matchInfoArea = document.getElementById('matchInfoArea');
    if (!matchInfoArea) {
        console.error('matchInfoArea not found!');
        return;
    }

    const matchId = matchInfoArea.dataset.matchId;
    const isLive = matchInfoArea.dataset.matchStatus === 'in_progress';

    console.log('Match setup:', { matchId, isLive, status: matchInfoArea.dataset.matchStatus });

    if (isLive) {
        console.log('Match is live, attempting WebSocket connection...');
        
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${wsScheme}://${window.location.host}/ws/match/${matchId}/`;
        console.log('WebSocket URL:', wsUrl);
        
        const matchSocket = new WebSocket(wsUrl);

        matchSocket.onopen = function(e) {
            console.log('WebSocket connection established successfully!');
        };

        matchSocket.onclose = function(e) {
            console.log('WebSocket connection closed:', e.code, e.reason);
            console.error('Match socket closed unexpectedly');
        };

        matchSocket.onerror = function(e) {
            console.error('WebSocket error occurred:', e);
        };

        matchSocket.onmessage = function(e) {
            console.log('Received WebSocket message:', e.data);
            
            try {
                const data = JSON.parse(e.data);
                console.log('Parsed data:', data);
                
                // Обновляем время
                const timeElement = document.getElementById('matchTime');
                if (timeElement) {
                    timeElement.textContent = `${data.minute}'`;
                } else {
                    console.warn('matchTime element not found');
                }

                // Обновляем счет
                const scoreElement = document.getElementById('score');
                if (scoreElement) {
                    scoreElement.textContent = `${data.home_score} - ${data.away_score}`;
                } else {
                    console.warn('score element not found');
                }

                // Добавляем новые события
                if (data.events && data.events.length > 0) {
                    const eventsList = document.getElementById('originalEvents');
                    if (eventsList) {
                        const listGroup = eventsList.querySelector('.list-group');
                        if (listGroup) {
                            data.events.forEach(event => {
                                const eventDiv = document.createElement('div');
                                eventDiv.className = 'list-group-item';
                                
                                let icon = '📝';
                                if (event.event_type === 'goal') icon = '⚽';
                                else if (event.event_type === 'yellow_card') icon = '🟨';
                                else if (event.event_type === 'red_card') icon = '🟥';

                                eventDiv.innerHTML = `
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>${event.minute}'</strong> 
                                            <span class="event-icon">${icon}</span>
                                            ${event.description}
                                        </div>
                                    </div>
                                `;
                                
                                listGroup.insertBefore(eventDiv, listGroup.firstChild);
                            });
                        } else {
                            console.warn('list-group element not found in originalEvents');
                        }
                    } else {
                        console.warn('originalEvents element not found');
                    }
                }

                // Если матч завершен, перезагружаем страницу
                if (data.status === 'finished') {
                    console.log('Match finished, reloading page...');
                    location.reload();
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
                console.error('Raw message:', e.data);
            }
        };
    } else {
        console.log('Match is not live, skipping WebSocket setup');
    }
});