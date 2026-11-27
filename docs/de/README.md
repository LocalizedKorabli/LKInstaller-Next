<div align=center>
  
  <img width="200" alt="logo" src="https://github.com/user-attachments/assets/7bf8c1be-2abe-47d0-b8d9-78394a2a3312" />
  
  <h2>LK I18n Installer Next</h2>
  
  [![stars](https://img.shields.io/github/stars/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/stargazers)
  [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-purple.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
  [![release](https://img.shields.io/github/release/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/releases/latest)
  
  [![Quellcode](https://img.shields.io/badge/Quell-code-orange?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next)
  [![Discord](https://img.shields.io/discord/1275430075369656381?style=for-the-badge)](https://discord.gg/3d9k2mkWy4)
  [![QQ-Gruppe](https://img.shields.io/badge/QQ-Gruppe-red?style=for-the-badge)](https://qm.qq.com/q/oLZZH47TRA)

</div>

<details><summary style="font-size: 14px;">Languages🌐</summary>

**Deutsch** | [English](/docs/en/README.md) | [简体中文](/README.md) | [繁體中文](/docs/cht/README.md) | [Русский](/docs/ru/README.md) | [日本語](/docs/ja/README.md) | [Español](/docs/es/README.md)

</details>

*Diese Dokumentation wurde mithilfe von KI übersetzt. Fehler oder Unklarheiten sind möglich.*

## Einführung

**LK I18n Installer Next** (im Folgenden **LK Next**) ist eine vollständige Neuentwicklung des [LK I18n Installer](https://github.com/LocalizedKorabli/I18nInstallerGUI).

<details><summary style="font-size: 12px;">Neue Funktionen in LK Next</summary>
<h4>Neue Funktionen in LK Next im Vergleich zum vorherigen Installer:</h4>

- Unterstützt die Installation von **Lokalisierungspaketen** in mehreren Sprachen: Vereinfachtes Chinesisch, Traditionelles Chinesisch, Englisch, Japanisch, Deutsch und Spanisch;
- Unterstützt die Installation von Lokalisierungspaketen für den Mir-Korabley-Client auf Steam;
- Unterstützt die Deinstallation von Lokalisierungspaketen;
- Unterstützt die Installation des **Schriftoptimierungspakets** (Font Opt.). Diese Option ist standardmäßig aktiviert, wenn die Lokalisierungssprache auf Vereinfachtes Chinesisch, Traditionelles Chinesisch oder Japanisch eingestellt ist;
- Unterstützt Ein-Klick-Updates für die Anwendung selbst;
- Führt „**Instanzen**“ und „**Voreinstellungen (Presets)**“ ein, sodass für mehrere Spielclient-Instanzen gleichzeitig unterschiedliche Installations- oder Deinstallationsvorgänge ausgeführt werden können;
- Unterstützt die gleichzeitige Nutzung mehrerer **Download-Routen** mit Prioritätssortierung;
  - Unterstützte Routen:
    - Tencent (nur Font Opt. und App-Updates)
    - Cloudflare (nur Font Opt. und App-Updates)
    - Gitee (nur Lokalisierungs- und EE-Paket)
    - GitLab (nur Lokalisierungs- und EE-Paket)
    - GitHub (nur Lokalisierungs- und EE-Paket)
- Unterstützt detailliertere Proxy-Einstellungen;
- Unterstützt den Wechsel der Anwendungssprache sowie zwischen hellem und dunklem Design.

<h4>Funktionale Änderungen in LK Next im Vergleich zum vorherigen Installer:</h4>

- Die Versionserkennung wurde optimiert und installiert Lokalisierungspakete jetzt nur noch für aktive Versionen, die vom Remote-Repository definiert werden;
- Alle Inhalte werden nun im von Mir Korabley neu eingeführten `.mkmod`-Format installiert;
- **Lokalisierungs-Mod-Pakete** (L10n Mods) werden jetzt immer über den von Mir Korabley eingeführten „MO-Mounting“-Mechanismus installiert.

<h4>Entfernte Funktionen in LK Next im Vergleich zum vorherigen Installer:</h4>

- Die Funktion zur Installation von Lokalisierungspaketen für Global-/CN-Server wurde entfernt, da sie selten genutzt wurde und Nutzer leicht irreführte.

</details>

## LK Next herunterladen und installieren

### Download-Quellen
- [Offizielle Download-Seite](https://localizedkorabli.org/en/lk-next.html)

<details><summary style="font-size: 12px;"><b>Vorgehen bei blockierten Downloads im Browser</b></summary>

- Microsoft Edge („lki_setup.exe wird nicht häufig heruntergeladen. Stellen Sie sicher, dass Sie lki_setup.exe vertrauen, bevor Sie die Datei öffnen“):
  - Bewegen Sie den Mauszeiger über den Download-Eintrag, klicken Sie rechts auf das Drei-Punkte-Symbol (`...`) und wählen Sie **Beibehalten**;
  - Öffnen Sie im Popup „Stellen Sie sicher, dass Sie lki_setup.exe vertrauen“ das Dropdown-Menü neben der blauen Schaltfläche **Löschen** und klicken Sie auf **Trotzdem beibehalten**.

- Chrome (Verdächtiger Download blockiert):
  - Klicken Sie auf den Download-Eintrag und wählen Sie **Verdächtige Datei herunterladen**.

</details>

### Anwendung installieren
- Öffnen Sie das heruntergeladene Installationsprogramm, wählen Sie die Installationssprache (diese wird auch als Standardsprache für LK Next und die Lokalisierungspakete festgelegt) und folgen Sie den Anweisungen bis zum Abschluss der Installation.

## LK Next verwenden

### Kurzfassung (TL;DR)

Wenn Sie lediglich das Lokalisierungspaket ohne weitere Einstellungen installieren möchten, klicken Sie einfach unten links im Hauptfenster (Tab **Spiel**) auf die Schaltfläche **Installieren**.

### Instanzen

#### Was ist eine Instanz?

Ihr installierter Mir-Korabley-Client kann als „Instanz“ in die Anwendung importiert werden, um Lokalisierungspakete zu installieren.

#### Instanzen importieren

Beim ersten Start versucht die Anwendung automatisch, alle Mir-Korabley-Clients auf Ihrem Gerät zu scannen und als Instanzen zu importieren.

Falls Ihre gewünschte Instanz nicht in der Liste erscheint, stellen Sie bitte sicher, dass das Spiel vollständig installiert ist, und klicken Sie rechts in der Zeile „Spielinstanzen“ auf die Schaltfläche **Instanzen auf diesem PC automatisch importieren**.

Sollte die Instanz weiterhin nicht importiert werden, klicken Sie in derselben Zeile auf **Instanz importieren**, um den Spielordner manuell hinzuzufügen.

#### Instanzen verwalten

Alle aktuell importierten Spielinstanzen werden im Tab **Spiel** angezeigt.

Über die Schaltflächen im Tab **Spiel** können Sie Instanzen importieren, schnell bearbeiten, entfernen, sortieren, deren Ordner öffnen, das Spiel starten oder eine **Verknüpfung für automatische Updates** erstellen.

#### Instanz auswählen (für Details)

Klicken Sie auf den Namen einer Spielinstanz, um sie auszuwählen. Nach der Auswahl wird der Eintrag blau hervorgehoben. Im Tab **Erweitert** können Sie anschließend Details zur Instanz und zur aktuell gewählten Voreinstellung einsehen.

#### Instanz ankreuzen (für Installation/Deinstallation)

Aktivieren bzw. deaktivieren Sie das Kontrollkästchen links neben dem Instanzeintrag im Tab **Spiel**. Über das Kontrollkästchen in der Kopfzeile „Spielinstanzen“ können Sie alle Instanzen gleichzeitig an- oder abwählen.

Alle neu importierten Instanzen sind standardmäßig angekreuzt.

### Voreinstellungen (Presets)

#### Was ist eine Voreinstellung?

Eine Instanz kann mehrere „Voreinstellungen“ besitzen, die festlegen, **welche konkreten Aktionen bei der Installation von Lokalisierungspaketen für diese Instanz ausgeführt werden**:

- Welche **Sprache / Client-Variante** (Live/PT) des Lokalisierungspakets heruntergeladen und installiert wird;
- Ob das [**Experience Enhancement Pack (EE Pack)**](#experience-enhancement-pack-ee-pack) heruntergeladen und installiert wird;
- Ob das [**Schriftoptimierungspaket (Font Opt.)**](#schriftoptimierungspaket-font-opt) heruntergeladen und installiert wird;
- Ob [**Lokalisierungs-Mod-Pakete (L10n Mods)**](#lokalisierungs-mod-pakete-l10n-mods) geladen werden.

#### Standard-Voreinstellung

Jede Instanz besitzt eine **Standard-Voreinstellung**, deren Installationssprache standardmäßig auf **die Sprache eingestellt ist, die beim Importieren der Instanz in der Anwendung angezeigt wird**.

#### Voreinstellungen verwalten

Wählen Sie zunächst eine Spielinstanz aus und wechseln Sie in den Tab **Erweitert**.

Im Dropdown-Menü **Installationsvoreinstellung** im Bereich „Voreinstellungskonfiguration“ können Sie schnell zwischen den Voreinstellungen wechseln.

Ein Klick auf das Zahnrad-Symbol rechts neben dem Dropdown-Menü öffnet die Oberfläche **Voreinstellungen verwalten**.

Dort können Sie:
- Voreinstellungen für diese Instanz hinzufügen, bearbeiten oder löschen;
- Alle Optionen einer Voreinstellung anpassen;
- Eine **Verknüpfung für automatische Updates** für die aktuelle Voreinstellung erstellen.

### Anpassung

#### Experience Enhancement Pack (EE Pack)

Das Experience Enhancement Pack (EE Pack) ist eine Mod-Sammlung für Mir Korabley und enthält:
- [Eingabemethoden-Unterstützungs-Mod](https://bbs.nga.cn/read.php?tid=29102783);
- UI-Optimierungs-Mod auf Basis des Unbound-Frameworks;
- Übersetzungspatches für andere Mir-Korabley-Mods passend zur aktuellen Lokalisierungssprache;
- Einen Start-Logo-Patch mit dem Branding unseres Teams.

Das EE Pack wird standardmäßig installiert. Sie können dies unter **Voreinstellungen verwalten** jederzeit ein- oder ausschalten.

#### Schriftoptimierungspaket (Font Opt.)

Das Schriftoptimierungspaket enthält Schrift-Mods für Mir Korabley, darunter SrcWagon — eine neue Schriftart auf Basis der nativen Schriftarten „ALS Wagon“ und „Source Han Sans CN“, die Darstellung und Positionierung einzelner Zeichen korrigiert.

Wenn die Lokalisierungssprache Ihrer Voreinstellung auf **Vereinfachtes Chinesisch**, **Traditionelles Chinesisch** oder **Japanisch** eingestellt ist, wird das Schriftoptimierungspaket standardmäßig installiert. Sie können dies unter **Voreinstellungen verwalten** anpassen.

#### Lokalisierungs-Mod-Pakete (L10n Mods)

Lokalisierungs-Mod-Pakete (L10n Mods) dienen zur gezielten Anpassung einzelner Texte im Lokalisierungspaket. Informationen zur Erstellung finden Sie im [Beitrag im Mir-Korabley-Forum](https://forum.korabli.su/topic/162025-).

Sie können erstellte L10n Mods direkt oder als `.zip`-Archiv in den Ordner der aktuellen Voreinstellung legen (zu öffnen über das Ordner-Symbol in **Voreinstellungen verwalten**).

L10n Mods werden beim **nächsten** Installationsvorgang automatisch geladen.

Standardmäßig sind L10n Mods aktiviert; Sie können dies unter **Voreinstellungen verwalten** ändern.

### Anwendungseinstellungen

Im Tab **Einstellungen** können Sie:
- Einstellungen für **Darstellung**, **Download** und **Dateien** anpassen;
- Download-Cache und Protokolldateien leeren;
- Das Datenverzeichnis der Anwendung einsehen und öffnen.

### Über die App / Updates

Im Tab **Über** können Sie:
- Die Anwendungsversion einsehen und **Nach Updates suchen**;
- Über die Symbole für GitHub, QQ und Discord das Quellcode-Repository öffnen oder unseren Community-Gruppen beitreten;
- Über das violette „AGPL V3“-Symbol den vollständigen Lizenztext auf der offiziellen GNU-Website aufrufen.

## FAQ

### Was tun bei Anwendungsfehlern oder fehlgeschlagener Installation?

Bitte versuchen Sie zunächst [**Nach Updates suchen**](#über-die-app--updates) und installieren Sie das Lokalisierungspaket anschließend erneut.

Öffnen Sie den Tab **Einstellungen** und klicken Sie in der Zeile **App-Datenpfad** auf **Ordner öffnen**. Wechseln Sie dort in den Ordner `logs` und sichern Sie die neueste `.log`-Datei.

Sie können die Datei selbst prüfen oder sie über [GitHub Issues](https://github.com/LocalizedKorabli/LKInstaller-Next/issues) | [QQ-Gruppe](https://qm.qq.com/q/SUoZAcV442) | [Discord-Server](https://discord.gg/3d9k2mkWy4) einreichen, um Hilfe zu erhalten.

### Wo ist die Funktion für automatische Updates?

Siehe [Instanzen verwalten](#instanzen-verwalten) und [Voreinstellungen verwalten](#voreinstellungen-verwalten). Sie können im Tab **Spiel** oder unter **Voreinstellungen verwalten** eine **Verknüpfung für automatische Updates** erstellen.

### Was tun bei Fragen zum Lokalisierungspaket selbst?

Bitte suchen Sie im [Team-Portal](https://github.com/LocalizedKorabli#%E9%A1%B9%E7%9B%AE%E4%BC%A0%E9%80%81%E9%97%A8portal) das entsprechende Repository für Ihre Sprache und Client-Variante und melden Sie dort ein Issue.

Sie können sich auch unserer QQ-Gruppe oder unserem Discord-Server anschließen.

## Danksagungen

- Allen Nutzerinnen und Nutzern, die am internen Test dieses Projekts teilgenommen haben

- [Python](https://www.python.org/) — Die Programmiersprache dieser Anwendung

- [Tkinter](https://docs.python.org/3/library/tkinter.html) — Das GUI-Framework dieser Anwendung

- [Google Gemini](https://gemini.google.com/), [Claude Code](https://claude.ai/code) und [DeepSeek](https://deepseek.com/) — Haben die Entwicklungszeit dieser Anwendung um etwa 80 % verkürzt

- [Azure theme for ttk](https://github.com/rdbende/Azure-ttk-theme) — Das verwendete ttk-Design der Benutzeroberfläche

- [Inno Setup](https://jrsoftware.org/isinfo.php) und [Nuitka](https://nuitka.net/) — Für die komfortablen Paketierungswerkzeuge
