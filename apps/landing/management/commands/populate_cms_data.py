"""Populate CMS with initial data from hardcoded landing page content."""

from django.core.management.base import BaseCommand

from apps.landing.models import (
    EducationLevel,
    FAQItem,
    LandingStatistic,
    LandingSubject,
    LessonType,
    PageContent,
    PricingPackage,
    SchoolInfo,
    TeamMember,
    Testimonial,
    WhyUsCard,
)


class Command(BaseCommand):
    help = 'Populate CMS with initial data from hardcoded landing page content'

    def handle(self, *args, **options):
        self.stdout.write('Populating CMS data...')

        self.create_school_info()
        self.create_page_contents()
        self.create_faq_items()
        self.create_statistics()
        self.create_why_us_cards()
        self.create_subjects()
        self.create_pricing_packages()
        self.create_education_levels()
        self.create_lesson_types()
        self.create_team_members()
        self.create_testimonials()

        self.stdout.write(self.style.SUCCESS('CMS data populated successfully!'))

    def create_school_info(self):
        """Create or update school info."""
        school_info, created = SchoolInfo.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'Na Piątkę',
                'tagline': 'Korepetycje, które działają',
                'description': 'Profesjonalne korepetycje z matematyki, angielskiego, niemieckiego i polskiego. Pomagamy uczniom od szkoły podstawowej po maturę osiągać najlepsze wyniki.',
                'email': 'kontakt@napiatke.pl',
                'phone': '+48 123 456 789',
                'address': 'ul. Przykładowa 1',
                'city': 'Warszawa',
                'postal_code': '00-001',
                'latitude': 52.2297,
                'longitude': 21.0122,
                'opening_hours': {
                    'pon-pt': '14:00-20:00',
                    'sob': '9:00-15:00',
                    'niedz': 'zamknięte',
                },
                'social_media': {
                    'facebook': 'https://facebook.com/napiatke',
                    'instagram': 'https://instagram.com/napiatke',
                },
                'footer_text': 'Korepetycje z pasją i doświadczeniem. Pomagamy uczniom osiągać sukcesy edukacyjne.',
                'copyright_text': '© 2024 Na Piątkę. Wszelkie prawa zastrzeżone.',
            }
        )
        if created:
            self.stdout.write('  Created school info')
        else:
            self.stdout.write('  School info already exists')

    def create_page_contents(self):
        """Create page content sections."""
        contents = [
            {
                'page_key': 'hero',
                'title': 'Korepetycje, które działają',
                'subtitle': 'Matematyka, angielski i niemiecki – od podstawówki do matury.',
                'content': '',
            },
            {
                'page_key': 'about',
                'title': 'O nas',
                'subtitle': 'Skuteczna nauka z indywidualnym podejściem',
                'content': '''<p class="text-slate-600 leading-relaxed mb-4">
                    Jesteśmy zespołem doświadczonych korepetytorów, którzy z pasją pomagają uczniom
                    w nauce matematyki, języka angielskiego, niemieckiego i polskiego.
                </p>
                <p class="text-slate-600 leading-relaxed">
                    Nasze zajęcia to nie tylko przekazywanie wiedzy – to budowanie pewności siebie,
                    rozwijanie umiejętności samodzielnego myślenia i przygotowanie do egzaminów.
                </p>''',
            },
        ]
        for content in contents:
            PageContent.objects.get_or_create(
                page_key=content['page_key'],
                defaults={
                    'title': content['title'],
                    'subtitle': content['subtitle'],
                    'content': content['content'],
                    'is_active': True,
                }
            )
        self.stdout.write(f'  Created {len(contents)} page contents')

    def create_faq_items(self):
        """Create FAQ items."""
        faqs = [
            {
                'question': 'Jak wyglądają pakiety zajęć?',
                'answer': 'Oferujemy pakiety miesięczne: Mini (4 spotkania), Standard (8 spotkań), Intensywny (12 spotkań) i Premium (16 spotkań). Każde spotkanie trwa 60 minut. Ceny zależą od formy zajęć – indywidualnych lub grupowych.',
                'category': 'Pakiety',
                'order_index': 0,
            },
            {
                'question': 'Jak działa odrabianie nieobecności?',
                'answer': 'Odwołanie zajęć jest możliwe minimum 24 godziny przed planowanym terminem. Nieobecność można odrobić w ciągu 30 dni od daty odwołanych zajęć. Zapewniamy elastyczność i dostosowujemy terminy do Twoich możliwości.',
                'category': 'Nieobecności',
                'order_index': 1,
            },
            {
                'question': 'Ile osób jest w grupie?',
                'answer': 'Zajęcia grupowe odbywają się w grupach maksymalnie 4-osobowych. Dzięki temu każdy uczeń otrzymuje odpowiednią uwagę, a jednocześnie może korzystać z motywacji płynącej z nauki w grupie rówieśniczej.',
                'category': 'Zajęcia',
                'order_index': 2,
            },
            {
                'question': 'Jak długo trwa jedna lekcja?',
                'answer': 'Standardowa lekcja trwa 60 minut. To optymalny czas, który pozwala na efektywną pracę bez utraty koncentracji. W razie potrzeby możemy dostosować długość zajęć do indywidualnych potrzeb ucznia.',
                'category': 'Zajęcia',
                'order_index': 3,
            },
            {
                'question': 'Czy oferujecie zajęcia online?',
                'answer': 'Tak, oferujemy zajęcia zarówno stacjonarne, jak i online. Zajęcia online odbywają się przez platformę do wideokonferencji z wykorzystaniem tablicy wirtualnej. Materiały są udostępniane uczniom po każdych zajęciach.',
                'category': 'Zajęcia',
                'order_index': 4,
            },
            {
                'question': 'Jak mogę się zapisać?',
                'answer': 'Możesz się zapisać przez formularz kontaktowy na stronie, telefonicznie lub mailowo. Po kontakcie ustalimy poziom ucznia, cele nauki i dobierzemy odpowiednią grupę lub korepetytora do zajęć indywidualnych.',
                'category': 'Zapisy',
                'order_index': 5,
            },
            {
                'question': 'Czy jest możliwość lekcji próbnej?',
                'answer': 'Tak, oferujemy bezpłatną konsultację, podczas której poznamy potrzeby ucznia i przedstawimy propozycję współpracy. To świetna okazja, żeby sprawdzić, czy nasze podejście odpowiada oczekiwaniom.',
                'category': 'Zapisy',
                'order_index': 6,
            },
            {
                'question': 'Jak wygląda płatność?',
                'answer': 'Płatność za pakiet zajęć odbywa się z góry, przed rozpoczęciem miesiąca. Akceptujemy przelewy bankowe oraz płatności BLIK. Faktura wystawiana jest na życzenie.',
                'category': 'Płatności',
                'order_index': 7,
            },
        ]
        for faq in faqs:
            FAQItem.objects.get_or_create(
                question=faq['question'],
                defaults={
                    'answer': faq['answer'],
                    'category': faq['category'],
                    'order_index': faq['order_index'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(faqs)} FAQ items')

    def create_statistics(self):
        """Create landing page statistics."""
        stats = [
            {'value': '5+', 'label': 'lat doświadczenia', 'order_index': 0},
            {'value': '3', 'label': 'nowoczesne sale', 'order_index': 1},
            {'value': '100+', 'label': 'zadowolonych uczniów', 'order_index': 2},
        ]
        for stat in stats:
            LandingStatistic.objects.get_or_create(
                value=stat['value'],
                defaults={
                    'label': stat['label'],
                    'order_index': stat['order_index'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(stats)} statistics')

    def create_why_us_cards(self):
        """Create 'Why Us' cards."""
        cards = [
            {
                'title': 'Małe grupy do 4 osób',
                'description': 'Pełna uwaga dla każdego ucznia. Indywidualne podejście w kameralnej atmosferze.',
                'icon': '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
                'color': 'brand',
                'link': '#pakiety',
                'order_index': 0,
            },
            {
                'title': 'Lekcje 60 minut',
                'description': 'Konkret i systematyczność. Optymalna długość dla koncentracji i postępów.',
                'icon': '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
                'color': 'emerald',
                'link': '',
                'order_index': 1,
            },
            {
                'title': 'Pakiety miesięczne',
                'description': 'Elastyczne planowanie nauki dostosowane do Twoich potrzeb i terminarza.',
                'icon': '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
                'color': 'blue',
                'link': '#pakiety',
                'order_index': 2,
            },
            {
                'title': 'Doświadczeni korepetytorzy',
                'description': 'Indywidualne podejście oparte na latach praktyki i pasji do nauczania.',
                'icon': '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M12 11l2 2 4-4"/></svg>',
                'color': 'purple',
                'link': '#zespol',
                'order_index': 3,
            },
            {
                'title': 'Jasne zasady odwołań',
                'description': '≥24h przed zajęciami i możliwość odrobienia w ciągu 30 dni. Transparentnie.',
                'icon': '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4"/><path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"/><path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3"/></svg>',
                'color': 'orange',
                'link': '',
                'order_index': 4,
            },
            {
                'title': 'Dogodna lokalizacja',
                'description': 'Nowoczesne sale w świetnej lokalizacji. Wygodny dojazd i parking.',
                'icon': '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
                'color': 'teal',
                'link': '#kontakt',
                'order_index': 5,
            },
        ]
        for card in cards:
            WhyUsCard.objects.get_or_create(
                title=card['title'],
                defaults={
                    'description': card['description'],
                    'icon': card['icon'],
                    'color': card['color'],
                    'link': card['link'],
                    'order_index': card['order_index'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(cards)} "Why Us" cards')

    def create_subjects(self):
        """Create landing page subjects."""
        subjects = [
            {
                'name': 'Matematyka',
                'slug': 'matematyka',
                'short_description': 'Od podstaw arytmetyki po zaawansowane zagadnienia maturalne. Algebra, geometria, funkcje i statystyka.',
                'full_description': 'Kompleksowe przygotowanie z matematyki na każdym poziomie. Pomagamy zrozumieć trudne zagadnienia, przygotowujemy do egzaminów i budujemy solidne podstawy matematycznego myślenia.',
                'icon_svg': '<svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 12h18M12 3v18"/><circle cx="12" cy="12" r="2"/></svg>',
                'color_from': 'blue-500',
                'color_to': 'indigo-600',
                'levels': 'Wszystkie poziomy',
                'topics': ['Arytmetyka', 'Algebra', 'Geometria', 'Funkcje', 'Statystyka', 'Rachunek prawdopodobieństwa'],
                'target_groups': ['Szkoła podstawowa', 'Liceum', 'Technikum', 'Matura'],
                'order_index': 0,
                'is_featured': True,
            },
            {
                'name': 'Angielski',
                'slug': 'angielski',
                'short_description': 'Konwersacje, gramatyka i przygotowanie do egzaminów. Od podstaw do poziomu zaawansowanego.',
                'full_description': 'Nauka języka angielskiego dostosowana do Twoich celów. Rozwijamy wszystkie kompetencje językowe: mówienie, słuchanie, czytanie i pisanie.',
                'icon_svg': '<svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 7h16M4 12h10M4 17h16"/></svg>',
                'color_from': 'emerald-500',
                'color_to': 'teal-600',
                'levels': 'A1 - C2',
                'topics': ['Gramatyka', 'Konwersacje', 'Słownictwo', 'Pisanie', 'Egzaminy Cambridge', 'Matura'],
                'target_groups': ['Szkoła podstawowa', 'Liceum', 'Dorośli', 'Matura'],
                'order_index': 1,
                'is_featured': True,
            },
            {
                'name': 'Niemiecki',
                'slug': 'niemiecki',
                'short_description': 'Systematyczna nauka od podstaw. Przygotowanie do egzaminów Goethe-Institut i matury.',
                'full_description': 'Język niemiecki z naciskiem na praktyczne umiejętności komunikacyjne. Przygotowujemy do egzaminów i pomagamy w nauce gramatyki.',
                'icon_svg': '<svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 4h12v16H6z"/><path d="M10 8h4"/></svg>',
                'color_from': 'amber-500',
                'color_to': 'orange-600',
                'levels': 'A1 - C1',
                'topics': ['Gramatyka', 'Konwersacje', 'Słownictwo', 'Egzaminy Goethe', 'Matura'],
                'target_groups': ['Szkoła podstawowa', 'Liceum', 'Dorośli', 'Matura'],
                'order_index': 2,
                'is_featured': False,
            },
            {
                'name': 'Polski',
                'slug': 'polski',
                'short_description': 'Wypracowania, lektury i przygotowanie do matury. Rozwijamy umiejętności pisania i analizy tekstu.',
                'full_description': 'Język polski na każdym poziomie. Pomagamy w analizie lektur, pisaniu wypracowań i przygotowaniu do egzaminów.',
                'icon_svg': '<svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
                'color_from': 'red-500',
                'color_to': 'pink-600',
                'levels': 'Wszystkie poziomy',
                'topics': ['Gramatyka', 'Ortografia', 'Lektury', 'Wypracowania', 'Retoryka', 'Matura'],
                'target_groups': ['Szkoła podstawowa', 'Liceum', 'Matura'],
                'order_index': 3,
                'is_featured': False,
            },
        ]
        for subj in subjects:
            LandingSubject.objects.get_or_create(
                slug=subj['slug'],
                defaults={
                    'name': subj['name'],
                    'short_description': subj['short_description'],
                    'full_description': subj['full_description'],
                    'icon_svg': subj['icon_svg'],
                    'color_from': subj['color_from'],
                    'color_to': subj['color_to'],
                    'levels': subj['levels'],
                    'topics': subj['topics'],
                    'target_groups': subj['target_groups'],
                    'order_index': subj['order_index'],
                    'is_featured': subj['is_featured'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(subjects)} subjects')

    def create_pricing_packages(self):
        """Create pricing packages."""
        packages = [
            {
                'name': 'Mini',
                'sessions_count': 4,
                'individual_price': 240.00,
                'group_price': 160.00,
                'is_popular': False,
                'order_index': 0,
            },
            {
                'name': 'Standard',
                'sessions_count': 8,
                'individual_price': 460.00,
                'group_price': 300.00,
                'is_popular': True,
                'order_index': 1,
            },
            {
                'name': 'Intensywny',
                'sessions_count': 12,
                'individual_price': 660.00,
                'group_price': 420.00,
                'is_popular': False,
                'order_index': 2,
            },
            {
                'name': 'Premium',
                'sessions_count': 16,
                'individual_price': 840.00,
                'group_price': 560.00,
                'is_popular': False,
                'order_index': 3,
            },
        ]
        for pkg in packages:
            PricingPackage.objects.get_or_create(
                name=pkg['name'],
                defaults={
                    'sessions_count': pkg['sessions_count'],
                    'individual_price': pkg['individual_price'],
                    'group_price': pkg['group_price'],
                    'is_popular': pkg['is_popular'],
                    'order_index': pkg['order_index'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(packages)} pricing packages')

    def create_education_levels(self):
        """Create education levels."""
        levels = [
            {'name': 'Nauczanie wczesnoszkolne', 'color': 'emerald', 'order_index': 0},
            {'name': 'Szkoła podstawowa', 'color': 'blue', 'order_index': 1},
            {'name': 'Liceum / Technikum', 'color': 'purple', 'order_index': 2},
            {'name': 'Matura', 'color': 'red', 'order_index': 3},
        ]
        for level in levels:
            EducationLevel.objects.get_or_create(
                name=level['name'],
                defaults={
                    'color': level['color'],
                    'order_index': level['order_index'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(levels)} education levels')

    def create_lesson_types(self):
        """Create lesson types."""
        types = [
            {
                'name': 'Zajęcia indywidualne',
                'subtitle': '',
                'description': 'Pełna uwaga korepetytora skupiona na jednym uczniu. Indywidualny program i tempo nauki.',
                'icon_svg': '<svg class="h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
                'color': 'brand',
                'features': [
                    'Indywidualny program nauki',
                    'Elastyczne tempo',
                    '100% uwagi korepetytora',
                    'Dostosowanie do potrzeb ucznia',
                ],
                'order_index': 0,
            },
            {
                'name': 'Zajęcia grupowe',
                'subtitle': '(do 4 osób)',
                'description': 'Nauka w małej grupie. Motywacja rówieśnicza i atrakcyjna cena.',
                'icon_svg': '<svg class="h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
                'color': 'emerald',
                'features': [
                    'Maksymalnie 4 osoby w grupie',
                    'Motywacja rówieśnicza',
                    'Atrakcyjna cena',
                    'Wspólne rozwiązywanie problemów',
                ],
                'order_index': 1,
            },
        ]
        for lt in types:
            LessonType.objects.get_or_create(
                name=lt['name'],
                defaults={
                    'subtitle': lt['subtitle'],
                    'description': lt['description'],
                    'icon_svg': lt['icon_svg'],
                    'color': lt['color'],
                    'features': lt['features'],
                    'order_index': lt['order_index'],
                    'is_published': True,
                }
            )
        self.stdout.write(f'  Created {len(types)} lesson types')

    def create_team_members(self):
        """Create team members."""
        members = [
            {
                'name': 'Anna',
                'surname': 'Kowalska',
                'position': 'Matematyka',
                'bio': 'Doświadczony pedagog z 10-letnim stażem. Specjalizuje się w przygotowaniu do matury i olimpiad matematycznych.',
                'expertise': ['Matematyka', 'Matura', 'Olimpiady'],
                'order_index': 0,
            },
            {
                'name': 'Tomasz',
                'surname': 'Nowak',
                'position': 'Język angielski',
                'bio': 'Certyfikowany nauczyciel z doświadczeniem w nauczaniu wszystkich poziomów. Przygotowuje do egzaminów Cambridge.',
                'expertise': ['Angielski', 'FCE', 'CAE'],
                'order_index': 1,
            },
            {
                'name': 'Maria',
                'surname': 'Wiśniewska',
                'position': 'Język niemiecki',
                'bio': 'Absolwentka germanistyki z wieloletnim doświadczeniem. Przygotowuje do egzaminów Goethe-Institut.',
                'expertise': ['Niemiecki', 'Goethe', 'Matura'],
                'order_index': 2,
            },
        ]
        created_count = 0
        for member in members:
            _, created = TeamMember.objects.get_or_create(
                name=member['name'],
                surname=member['surname'],
                defaults={
                    'position': member['position'],
                    'bio': member['bio'],
                    'expertise': member['expertise'],
                    'order_index': member['order_index'],
                    'is_published': True,
                }
            )
            if created:
                created_count += 1
        self.stdout.write(f'  Created {created_count} team members')

    def create_testimonials(self):
        """Create testimonials."""
        testimonials = [
            {
                'student_name': 'Anna K.',
                'parent_name': 'Ewa K.',
                'content': 'Świetne podejście i jasne tłumaczenie zagadnień. Córka zyskała pewność siebie i poprawiła oceny już po kilku spotkaniach. Polecamy!',
                'rating': 5,
                'subject': 'Matematyka',
                'level': 'Matura',
                'display_order': 0,
            },
            {
                'student_name': 'Marek P.',
                'parent_name': 'Piotr P.',
                'content': 'Bardzo dobra organizacja i przejrzyste zasady. Syn polubił matematykę, a wyniki testów wyraźnie wzrosły. Dziękujemy!',
                'rating': 5,
                'subject': 'Matematyka',
                'level': 'Szkoła podstawowa',
                'display_order': 1,
            },
            {
                'student_name': 'Kasia L.',
                'parent_name': '',
                'content': 'Angielski prowadzony ciekawie, dużo mówienia i praktyki. Doceniam elastyczne terminy i szybki kontakt.',
                'rating': 5,
                'subject': 'Angielski',
                'level': 'Liceum',
                'display_order': 2,
            },
            {
                'student_name': 'Jakub M.',
                'parent_name': 'Agnieszka M.',
                'content': 'Przygotowanie do matury z matematyki na najwyższym poziomie. Syn zdał z wynikiem 90%. Gorąco polecam!',
                'rating': 5,
                'subject': 'Matematyka',
                'level': 'Matura',
                'display_order': 3,
            },
            {
                'student_name': 'Zofia W.',
                'parent_name': '',
                'content': 'Fantastyczne zajęcia z niemieckiego. W końcu rozumiem gramatykę, która wcześniej była dla mnie koszmarem.',
                'rating': 5,
                'subject': 'Niemiecki',
                'level': 'Liceum',
                'display_order': 4,
            },
        ]
        created_count = 0
        for testimonial in testimonials:
            _, created = Testimonial.objects.get_or_create(
                student_name=testimonial['student_name'],
                subject=testimonial['subject'],
                defaults={
                    'parent_name': testimonial['parent_name'],
                    'content': testimonial['content'],
                    'rating': testimonial['rating'],
                    'level': testimonial['level'],
                    'display_order': testimonial['display_order'],
                    'is_verified': True,
                    'is_published': True,
                }
            )
            if created:
                created_count += 1
        self.stdout.write(f'  Created {created_count} testimonials')
