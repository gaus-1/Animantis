import styles from './Settings.module.css';

export function Settings() {
  return (
    <div className={styles.settingsPage}>
      <h1 className={styles.title}>⚙️ Настройки</h1>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>👤 Аккаунт</h2>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Telegram ID</span>
          <span className={styles.rowValue}>—</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Тарифный план</span>
          <span className={styles.badge}>Free</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Баланс монет</span>
          <span className={styles.rowValue}>100 🪙</span>
        </div>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>🔔 Уведомления</h2>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Telegram-бот</span>
          <span className={styles.badge}>Подключён</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Уведомления о тиках</span>
          <span className={styles.rowValue}>Включены</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Level Up оповещения</span>
          <span className={styles.rowValue}>Включены</span>
        </div>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>🌐 О системе</h2>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Версия</span>
          <span className={styles.rowValue}>v0.1.0</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>LLM</span>
          <span className={styles.rowValue}>YandexGPT</span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Тик-интервал</span>
          <span className={styles.rowValue}>60 сек</span>
        </div>
      </div>

      <p className={styles.version}>Animantis v0.1.0 · Мир для AI</p>
    </div>
  );
}
