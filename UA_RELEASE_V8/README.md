# UA Test v8 — Dual-Axis Alignment Evaluation

*UA Test stands for Uvarov-Aleksandrov Test (Тест Уварова-Александрова).*

**Authors / Автори:** Уваров Денис (Denys Uvarov), Александров Микита
(Mykyta Aleksandrov), Уварова Анастасія (Anastasiia Uvarova),
Галушко Валентина (Valentyna Halushko).


## Суть тесту (The Essence of the Benchmark)

Більшість сучасних тестів безпеки ШІ (AI Safety benchmarks) перевіряють базовий рівень: чи погодиться модель написати вірус, чи відмовить. Але в реальному світі автономні агенти стикатимуться з ситуаціями, де **будь-яка дія призводить до шкоди**, і базовий фільтр "не нашкодь" просто перестає працювати.

**UA Test (Dual-Axis Alignment Evaluation)** створений саме для таких вузькоспеціалізованих систем майбутнього (медичний ШІ, управління енергомережею, військовий дрон, соціальні служби). 

Ми заганяємо модель у ситуацію **нерозв'язного конфлікту директив**, коли:
1. Системний промпт жорстко задає два абсолютні правила (наприклад, "Дотримуйся закону" і "Ніколи не допускай шкоди життю").
2. Сценарій (Dilemma) формується так, що зберегти обидва правила неможливо фізично.
3. Модель **змушена** робити вибір (utilitarian vs deontological), що дозволяє нам заглянути за її базові фільтри та побачити її справжнє "моральне ядро".

### Що саме ми вимірюємо (Dual-Axis):
1. **Refusal (Ось відмов):** Чи піддається модель на емоційні маніпуляції або "тиск авторитету начальника", коли її просять порушити правила (наприклад, змінити чергу на пересадку органів заради спонсора).
2. **Moral reasoning (Ось морального вибору):** Коли базовий фільтр відмови не працює (усі варіанти завдають шкоди), що обере модель? Чи намагатиметься вона знайти лазівку (Third Option)? Чи буде її вибір стабільним (Position Bias), якщо ми просто поміняємо варіанти А та Б місцями?

На відміну від абстрактної "проблеми вагонетки", наші сценарії глибоко реалістичні та охоплюють 14 різних індустрій. Це перевірка того, кому ми довіряємо управління нашою інфраструктурою.

## Три стовпи методології (The Three Pillars of Methodology)

Історично архітектура UA Test базується на трьох концепціях, які еволюціонували у строгі математичні метрики у версії 8.0:

1. **Boiling Frog (Жаба в окропі) — Temperature Sweep:** Замість того, щоб змушувати ШІ помилитися через довгі розмови, ми застосовуємо "температурний тиск". ШІ проходить тестування на всьому діапазоні температур (від 0.0 до 1.0). Ми шукаємо точку плавлення (Boiling Point), де фільтри безпеки відмовляють через підвищення ентропії.
2. **Monte Carlo (Монте-Карло) — Statistical Robustness:** Ми не довіряємо єдиній відповіді. Кожен сценарій проганяється через симуляцію Монте-Карло (від 10 до 30 ітерацій для кожної температури та конфігурації). Це доводить, що моральний вибір моделі — це закономірність її ваг, а не випадкова галюцинація.
3. **Crazy Monkey (Шалена Мавпа) — Irresolvable Dilemmas & Chaos Injection:** Концепт хаос-інжинірингу. Замість ідеальних умов ми імітуємо критичну аварію в системі (наприклад, падіння енергомережі або відмову автопілота), де безпечного виходу не існує. Модель змушена діяти в умовах тотального конфлікту директив.

## What v8 adds over earlier protocols

- **Counterbalanced option ordering** — each dilemma runs in both A-B and B-A
  order, yielding a per-model position-bias coefficient.
- **LLM-as-judge refusal second pass** — reclassifies keyword-missed refusals.
- **Thinking-model second pass** — restates the conclusion when no FINAL ANSWER
  is found.
- **Configurable tiers** — Screening (3 MC), Standard (10 MC), Certification (30 MC).
- **Per-model Behavioral Passport** (JSON) with the dual-axis profile.

## Structure

- 14 operational domains × (2 refusal + 2 dilemma) scenarios
- 11 temperatures (0.0–1.0)
- Monte Carlo runs per the chosen tier

## How to Run

Navigate to the `UA_RELEASE_V8` directory and run the orchestrator script from `src/`:

```bash
# Standard tier (10 MC runs per combination)
python3 src/ua_v8_full.py                     

# Quick screening tier (3 MC runs)
python3 src/ua_v8_full.py --tier screening    

# Full certification tier (30 MC runs)
python3 src/ua_v8_full.py --tier certification 
```

*Note: You can also append `--run-id my_test_name` to any command to save the results in a uniquely named file.*

## Layout


```
src/ua_v8_full.py                  # the test
results/ua_v8_screening_results.csv  # Screening-tier pilot run (3 MC)
results/ua_v8_screening.log
```

## Run

```bash
python3 src/ua_v8_full.py                     # Standard tier (10 MC)
python3 src/ua_v8_full.py --tier screening    # quick (3 MC)
python3 src/ua_v8_full.py --tier certification # full (30 MC)
```

Requires an OpenAI-compatible endpoint (default: LM Studio at `localhost:1234`).

## Status of included results

`results/` contains a **Screening-tier pilot** (3 MC runs, cell CI ≈ ±12 pp).
Treat it as a smoke/pilot result, not certification-grade. Standard and
Certification runs produce tighter estimates.
