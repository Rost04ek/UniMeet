// Переклад статусів
const statusTranslations = {
    'upcoming': 'Майбутня',
    'ongoing': 'Поточна',
    'completed': 'Завершена',
    'cancelled': 'Скасована'
};

// Функція для перекладу статусу
function translateStatus(status) {
    return statusTranslations[status] || status;
}

// Автоматичне приховування сповіщень
document.addEventListener('DOMContentLoaded', function() {
    // Показ/приховування пароля
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.dataset.target;
            const input = document.getElementById(targetId);
            const isPassword = input.type === 'password';
            
            input.type = isPassword ? 'text' : 'password';
            this.textContent = isPassword ? '◡' : '👁';
        });
    });

    // Перевірка збігу паролів при відправці форми
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const passwordConfirm = document.getElementById('password_confirm');
            
            if (password && passwordConfirm && password.value !== passwordConfirm.value) {
                e.preventDefault();
                
                // Видалимо старі повідомлення про помилку
                const oldErrors = document.querySelectorAll('.password-error');
                oldErrors.forEach(err => err.remove());
                
                // Додаємо нове повідомлення про помилку
                const errorMsg = document.createElement('div');
                errorMsg.className = 'password-error alert alert-danger';
                errorMsg.textContent = 'Паролі не збігаються! Перевірте введені паролі.';
                
                // Вставляємо перед кнопкою відправки
                const submitBtn = form.querySelector('button[type="submit"]');
                form.insertBefore(errorMsg, submitBtn);
                
                // Скролимо до помилки
                errorMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                
                // Видаляємо помилку через 5 секунд
                setTimeout(() => {
                    errorMsg.remove();
                }, 5000);
            }
        });
    }

    // Темна/світла тема
    const themeToggle = document.getElementById('theme-toggle');

    function setTheme(isDark) {
        document.body.classList.toggle('dark-theme', isDark);
        if (themeToggle) {
            themeToggle.textContent = isDark ? '☀️' : '🌙';
            themeToggle.setAttribute('aria-label', isDark ? 'Світла тема' : 'Темна тема');
        }
    }

    const storedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialDark = storedTheme ? storedTheme === 'dark' : prefersDark;
    setTheme(initialDark);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const isDark = !document.body.classList.contains('dark-theme');
            setTheme(isDark);
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }

    // Приховування алертів через 5 секунд
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // Підтвердження видалення
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Ви впевнені, що хочете видалити?')) {
                e.preventDefault();
            }
        });
    });
    
    // Валідація форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = 'var(--danger-color)';
                } else {
                    field.style.borderColor = 'var(--border-color)';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Будь ласка, заповніть всі обов\'язкові поля');
            }
        });
    });
    
    // Мобільне меню
    const navToggle = document.createElement('button');
    navToggle.className = 'nav-toggle';
    navToggle.innerHTML = '☰';
    navToggle.style.display = 'none';
    
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.parentNode.insertBefore(navToggle, navMenu);
        
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Адаптивне меню для мобільних пристроїв
    function checkScreenSize() {
        if (window.innerWidth <= 768) {
            navToggle.style.display = 'block';
        } else {
            navToggle.style.display = 'none';
            navMenu.classList.remove('active');
        }
    }
    
    window.addEventListener('resize', checkScreenSize);
    checkScreenSize();

    // Дата/час пікер (flatpickr) з підтримкою тем
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    if (datetimeInputs.length && window.flatpickr) {
        datetimeInputs.forEach(input => {
            window.flatpickr(input, {
                enableTime: true,
                dateFormat: "Y-m-d\TH:i",
                time_24hr: true,
                locale: window.flatpickr.l10ns.uk || 'uk',
                allowInput: true
            });
        });
    }

    // Карусель подій (6 найближчих) — нескінченна циклічна прокрутка
    const carouselTracks = document.querySelectorAll('[data-carousel]');
    carouselTracks.forEach(track => {
        const prevBtn = track.parentElement.querySelector('.carousel-btn.prev');
        const nextBtn = track.parentElement.querySelector('.carousel-btn.next');
        const card = track.querySelector('.event-card');
        if (!card) return;
        const cardWidth = card.getBoundingClientRect().width + 24;
        const originals = Array.from(track.children);

        // Нескінченно дублюємо одні й ті ж события
        function addMoreClones() {
            originals.forEach(orig => {
                const clone = orig.cloneNode(true);
                track.appendChild(clone);
            });
        }

        // Стартуємо з багатьма копіями
        for (let i = 0; i < 10; i++) {
            addMoreClones();
        }

        function scrollByAmount(dir) {
            track.scrollBy({ left: dir * cardWidth, behavior: 'smooth' });
            
            // Коли близько до кінця, додай ще копій
            setTimeout(() => {
                const remaining = track.scrollWidth - track.scrollLeft - track.clientWidth;
                if (remaining < cardWidth * 5) {
                    addMoreClones();
                }
            }, 100);
        }

        if (prevBtn) prevBtn.addEventListener('click', () => scrollByAmount(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => scrollByAmount(1));

        // Слідкуй за скролом для дин. додавання клонів
        track.addEventListener('scroll', () => {
            clearTimeout(track._addTimer);
            track._addTimer = setTimeout(() => {
                const remaining = track.scrollWidth - track.scrollLeft - track.clientWidth;
                if (remaining < cardWidth * 5) {
                    addMoreClones();
                }
            }, 100);
        });
    });
});

// Функція для форматування дати
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    };
    return date.toLocaleDateString('uk-UA', options);
}

// Функція для підрахунку часу до події
function timeUntilEvent(eventDate) {
    const now = new Date();
    const event = new Date(eventDate);
    const diff = event - now;
    
    if (diff < 0) {
        return 'Подія завершена';
    }
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (days > 0) {
        return `За ${days} днів`;
    } else if (hours > 0) {
        return `За ${hours} годин`;
    } else {
        return 'Скоро';
    }
}

// Анімація появи елементів при прокручуванні
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateX(0)';
        } else {
            entry.target.style.opacity = '0';
            entry.target.style.transform = 'translateX(24px)';
        }
    });
}, observerOptions);

// Застосування анімацій до карток
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.event-card, .feature-card, .category-card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateX(24px)';
        card.style.transition = 'opacity 0.5s, transform 0.5s';
        observer.observe(card);
    });
});

// Функція для пошуку подій
function searchEvents(query) {
    const events = document.querySelectorAll('.event-card, .event-card-large');
    query = query.toLowerCase();
    
    events.forEach(event => {
        const title = event.querySelector('h3').textContent.toLowerCase();
        const description = event.querySelector('.event-description')?.textContent.toLowerCase() || '';
        
        if (title.includes(query) || description.includes(query)) {
            event.style.display = '';
        } else {
            event.style.display = 'none';
        }
    });
}

// Налаштування 24-годинного формату для календарів з flatpickr
document.addEventListener('DOMContentLoaded', () => {
    const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
    
    dateInputs.forEach(input => {
        flatpickr(input, {
            enableTime: true,
            time_24hr: true,
            dateFormat: "Y-m-d H:i",
            altInput: true,
            altFormat: "d.m.Y H:i",
            locale: "uk",
            minuteIncrement: 5
        });
    });

    // Кастомний autocomplete для університетів
    const universityInput = document.getElementById('university');
    const dropdown = document.getElementById('university-dropdown');
    
    if (universityInput && dropdown) {
        const items = Array.from(dropdown.querySelectorAll('.autocomplete-item'));
        let currentFocus = -1;

        universityInput.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            currentFocus = -1;
            
            if (!value) {
                dropdown.classList.remove('show');
                return;
            }

            let hasResults = false;
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(value)) {
                    item.style.display = 'block';
                    hasResults = true;
                } else {
                    item.style.display = 'none';
                }
            });

            dropdown.classList.toggle('show', hasResults);
        });

        universityInput.addEventListener('focus', function() {
            if (this.value) {
                dropdown.classList.add('show');
            }
        });

        universityInput.addEventListener('keydown', function(e) {
            const visibleItems = items.filter(item => item.style.display !== 'none');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentFocus++;
                if (currentFocus >= visibleItems.length) currentFocus = 0;
                setActive(visibleItems);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentFocus--;
                if (currentFocus < 0) currentFocus = visibleItems.length - 1;
                setActive(visibleItems);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (currentFocus > -1 && visibleItems[currentFocus]) {
                    visibleItems[currentFocus].click();
                }
            } else if (e.key === 'Escape') {
                dropdown.classList.remove('show');
            }
        });

        function setActive(visibleItems) {
            items.forEach(item => item.classList.remove('active'));
            if (visibleItems[currentFocus]) {
                visibleItems[currentFocus].classList.add('active');
                visibleItems[currentFocus].scrollIntoView({ block: 'nearest' });
            }
        }

        items.forEach(item => {
            item.addEventListener('click', function() {
                universityInput.value = this.dataset.value;
                dropdown.classList.remove('show');
                currentFocus = -1;
            });
        });

        document.addEventListener('click', function(e) {
            if (!universityInput.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
    }

    // Підтвердження виходу
    const logoutLink = document.querySelector('a[href*="logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            if (!confirm('Ви впевнені, що хочете вийти?')) {
                e.preventDefault();
            }
        });
    }
});

// Експорт функцій для використання в інших скриптах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDate,
        timeUntilEvent,
        searchEvents
    };
}
