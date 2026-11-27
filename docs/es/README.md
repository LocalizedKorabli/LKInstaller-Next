<div align=center>
  
  <img width="200" alt="logo" src="https://github.com/user-attachments/assets/7bf8c1be-2abe-47d0-b8d9-78394a2a3312" />
  
  <h2>LK I18n Installer Next</h2>
  
  [![stars](https://img.shields.io/github/stars/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/stargazers)
  [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-purple.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
  [![release](https://img.shields.io/github/release/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/releases/latest)
  
  [![Código fuente](https://img.shields.io/badge/Código-Fuente-orange?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next)
  [![Discord](https://img.shields.io/discord/1275430075369656381?style=for-the-badge)](https://discord.gg/3d9k2mkWy4)
  [![Grupo QQ](https://img.shields.io/badge/QQ-Grupo-red?style=for-the-badge)](https://qm.qq.com/q/oLZZH47TRA)

</div>

<details><summary style="font-size: 14px;">Languages🌐</summary>

**Español** | [English](/docs/en/README.md) | [简体中文](/README.md) | [繁體中文](/docs/cht/README.md) | [Русский](/docs/ru/README.md) | [日本語](/docs/ja/README.md) | [Deutsch](/docs/de/README.md)

</details>

*Esta documentación fue traducida con IA. Pueden existir errores o ambigüedades.*

## Introducción

**LK I18n Installer Next** (en adelante **LK Next**) es una reescritura completa de [LK I18n Installer](https://github.com/LocalizedKorabli/I18nInstallerGUI).

<details><summary style="font-size: 12px;">Nuevas funciones en LK Next</summary>
<h4>Nuevas funciones introducidas en LK Next respecto al instalador anterior:</h4>

- Compatible con la instalación de **paquetes de localización** en varios idiomas: chino simplificado, chino tradicional, inglés, japonés, alemán y español;
- Compatible con la instalación de paquetes de localización para el cliente de Mir Korabley en Steam;
- Compatible con la desinstalación de paquetes de localización;
- Compatible con la instalación del **paquete de optimización de fuentes** (Font Opt.). Esta opción está activada por defecto cuando el idioma de localización es chino simplificado, chino tradicional o japonés;
- Compatible con actualizaciones en un clic para la propia aplicación;
- Introduce «**Instancias**» y «**Preajustes (Presets)**», lo que permite realizar diferentes operaciones de instalación o desinstalación simultáneamente para múltiples instancias del cliente del juego;
- Compatible con el uso simultáneo de múltiples **rutas de descarga** con ordenación por prioridad;
  - Rutas compatibles:
    - Tencent (solo Font Opt. y actualizaciones de la aplicación)
    - Cloudflare (solo Font Opt. y actualizaciones de la aplicación)
    - Gitee (solo paquetes de localización y EE Pack)
    - GitLab (solo paquetes de localización y EE Pack)
    - GitHub (solo paquetes de localización y EE Pack)
- Compatible con ajustes de proxy más detallados;
- Compatible con el cambio de idioma de la interfaz y temas Claro/Oscuro.

<h4>Cambios funcionales en LK Next respecto al instalador anterior:</h4>

- Se ha optimizado el mecanismo de detección de versiones y ahora solo instala paquetes de localización para las versiones activas definidas por el repositorio remoto;
- Todo el contenido se instala ahora en el formato `.mkmod` introducido por Mir Korabley;
- Los **paquetes de modificación de localización** (L10n Mods) se instalan ahora siempre mediante el mecanismo «MO mounting» introducido por Mir Korabley.

<h4>Funciones eliminadas en LK Next respecto al instalador anterior:</h4>

- Se ha eliminado la función para instalar paquetes de localización en servidores Global/CN, ya que apenas se utilizaba y podía inducir a error.

</details>

## Descargar e instalar LK Next

### Rutas de descarga
- [Página oficial de descarga](https://localizedkorabli.org/en/lk-next.html)

<details><summary style="font-size: 12px;"><b>Cómo actuar si el navegador bloquea la descarga</b></summary>

- Microsoft Edge («lki_setup.exe no se descarga habitualmente. Asegúrese de que confía en lki_setup.exe antes de abrirlo»):
  - Pase el cursor sobre la descarga, haga clic en el icono de tres puntos (`...`) a la derecha y seleccione **Conservar**;
  - En la ventana «Asegúrese de que confía en lki_setup.exe», abra el menú desplegable junto al botón azul **Eliminar** y haga clic en **Conservar de todos modos**.

- Chrome (Descarga sospechosa bloqueada):
  - Haga clic en el elemento descargado y seleccione **Descargar archivo sospechoso**.

</details>

### Instalar la aplicación
- Abra el instalador descargado, seleccione el idioma de instalación (este también se establecerá como idioma predeterminado de LK Next y de los paquetes de localización) y siga las instrucciones hasta completar la instalación.

## Usar LK Next

### Resumen rápido (TL;DR)

Si solo desea instalar el paquete de localización sin realizar ajustes adicionales, haga clic directamente en el botón **Instalar** situado en la parte inferior izquierda de la pantalla principal (pestaña **Juego**).

### Instancias

#### ¿Qué es una instancia?

Su cliente instalado de Mir Korabley puede importarse en la aplicación como una «Instancia» para instalar paquetes de localización.

#### Importar instancias

En el primer inicio, la aplicación intentará escanear todos los clientes de Mir Korabley en su equipo e importarlos como instancias.

Si la instancia deseada no aparece en la lista, asegúrese de que el juego esté completamente instalado y haga clic en el botón **Importar instancias automáticamente** situado en el extremo derecho de la fila «Instancias del juego».

Si aun así no se importa, haga clic en el botón **Importar instancia** en esa misma fila para intentar importarla manualmente.

#### Administrar instancias

Puede ver todas las instancias de juego importadas en la pestaña **Juego**.

También puede utilizar los demás botones de la pestaña **Juego** para importar, editar rápidamente, eliminar, ordenar, abrir la carpeta, iniciar el juego o generar un **acceso directo de actualización automática**.

#### Seleccionar una instancia (para ver detalles)

Haga clic en el nombre de una instancia para seleccionarla. Al seleccionarla, quedará resaltada en azul. Puede cambiar a la pestaña **Avanzado** para ver los detalles de la instancia y del preajuste seleccionado.

#### Marcar una instancia (para instalar/desinstalar)

Marque o desmarque la casilla situada a la izquierda de cada instancia en la pestaña **Juego**. Al hacer clic en la casilla de la fila «Instancias del juego», se marcarán o desmarcarán todas a la vez.

Todas las instancias recién importadas quedan marcadas por defecto.

### Preajustes (Presets)

#### ¿Qué es un preajuste?

Una instancia puede tener varios «Preajustes», que determinan **las operaciones específicas que realizará la aplicación al instalar los paquetes de localización para esa instancia**:

- Qué **idioma y tipo de cliente** (Live/PT) del paquete de localización se descargará e instalará;
- Si se descargará e instalará el [**Experience Enhancement Pack (EE Pack)**](#experience-enhancement-pack-ee-pack);
- Si se descargará e instalará el [**paquete de optimización de fuentes (Font Opt.)**](#paquete-de-optimización-de-fuentes-font-opt);
- Si se cargarán [**paquetes de modificación de localización (L10n Mods)**](#paquetes-de-modificación-de-localización-l10n-mods).

#### Preajuste predeterminado

Cada instancia tiene un **Preajuste predeterminado**, cuyo idioma de instalación se establece por defecto en **el idioma que la aplicación está mostrando cuando el usuario importa la instancia**.

#### Administrar preajustes

Para administrar los preajustes, primero seleccione una instancia de juego y cambie a la pestaña **Avanzado**.

En el menú desplegable **Preajuste de instalación** dentro del bloque de configuración, puede cambiar rápidamente de preajuste.

Al hacer clic en el botón del engranaje a la derecha del menú desplegable se abrirá la ventana **Administrar preajustes**.

En ella podrá:
- Añadir, modificar o eliminar preajustes de esta instancia;
- Ajustar todas las opciones de un preajuste;
- Generar un **acceso directo de actualización automática** para el preajuste actual.

### Personalización

#### Experience Enhancement Pack (EE Pack)

El Experience Enhancement Pack (EE Pack) es un conjunto de mods para Mir Korabley que incluye:
- [Mod de soporte de método de entrada](https://bbs.nga.cn/read.php?tid=29102783);
- Mod de optimización de interfaz basado en el framework Unbound;
- Parches de traducción para otros mods de Mir Korabley según el idioma de localización actual;
- Un parche de logotipo inicial con la marca de nuestro equipo.

El EE Pack se instala por defecto. Puede activar o desactivar su instalación desde **Administrar preajustes**.

#### Paquete de optimización de fuentes (Font Opt.)

El paquete de optimización de fuentes contiene mods tipográficos para Mir Korabley, incluido SrcWagon —una nueva fuente basada en las fuentes nativas «ALS Wagon» y «Source Han Sans CN»— que corrige la apariencia y posición de ciertos glifos.

Cuando el idioma de localización del preajuste sea **chino simplificado**, **chino tradicional** o **japonés**, este paquete se instalará por defecto. Puede cambiar esta opción en **Administrar preajustes**.

#### Paquetes de modificación de localización (L10n Mods)

Los paquetes de modificación de localización (L10n Mods) sirven para modificar textos específicos del paquete de localización. Para más información sobre cómo crearlos, consulte la [publicación en el foro de Mir Korabley](https://forum.korabli.su/topic/162025-).

Puede arrastrar y soltar sus L10n Mods directamente o empaquetados en un archivo `.zip` dentro de la carpeta correspondiente al preajuste actual (que se abre mediante el icono de carpeta en **Administrar preajustes**).

Los L10n Mods se cargarán la **próxima vez** que instale el paquete de localización.

Los L10n Mods están activados por defecto; puede cambiarlo en **Administrar preajustes**.

### Ajustes de la aplicación

En la pestaña **Ajustes** puede:
- Configurar las opciones de **Apariencia**, **Descarga** y **Archivos**;
- Limpiar la caché de descargas y los archivos de registro;
- Consultar y abrir el directorio de datos de la aplicación.

### Información / Actualizar aplicación

En la pestaña **Acerca de** puede:
- Ver la versión de la aplicación y **Buscar actualizaciones**;
- Visitar el repositorio del código fuente o unirse a nuestros grupos mediante los iconos de GitHub, QQ y Discord;
- Ver el texto completo de la licencia haciendo clic en el icono morado «AGPL V3» sobre el aviso de copyright.

## Preguntas frecuentes (Q&A)

### ¿Qué hago si la aplicación muestra un error o falla la instalación?

Pruebe primero a [**Buscar actualizaciones**](#información--actualizar-aplicación) y vuelva a instalar el paquete de localización.

Vaya a la pestaña **Ajustes** y haga clic en **Abrir dir.** en la fila **Ruta de datos**. En la carpeta abierta, entre en `logs` y guarde el archivo `.log` más reciente.

Puede revisarlo por su cuenta o enviarlo a [GitHub Issues](https://github.com/LocalizedKorabli/LKInstaller-Next/issues) | [Grupo QQ](https://qm.qq.com/q/SUoZAcV442) | [Servidor de Discord](https://discord.gg/3d9k2mkWy4) para recibir ayuda.

### ¿Dónde está la función de actualización automática?

Consulte [Administrar instancias](#administrar-instancias) y [Administrar preajustes](#administrar-preajustes). Puede generar un **acceso directo de actualización automática** desde la pestaña **Juego** o desde **Administrar preajustes**.

### ¿Qué hago si tengo dudas sobre el paquete de localización en sí?

Busque el repositorio correspondiente a su idioma y tipo de cliente en el [Portal del equipo](https://github.com/LocalizedKorabli#%E9%A1%B9%E7%9B%AE%E4%BC%A0%E9%80%81%E9%97%A8portal) y abra un Issue allí.

También puede unirse a nuestro grupo de QQ o servidor de Discord.

## Créditos

- A todos los usuarios que participaron en las pruebas internas de este proyecto

- [Python](https://www.python.org/) — El lenguaje de programación utilizado en esta aplicación

- [Tkinter](https://docs.python.org/3/library/tkinter.html) — El framework de interfaz gráfica utilizado

- [Google Gemini](https://gemini.google.com/), [Claude Code](https://claude.ai/code) y [DeepSeek](https://deepseek.com/) — Redujeron el tiempo de desarrollo en aproximadamente un 80 %

- [Azure theme for ttk](https://github.com/rdbende/Azure-ttk-theme) — El tema ttk utilizado en la interfaz

- [Inno Setup](https://jrsoftware.org/isinfo.php) y [Nuitka](https://nuitka.net/) — Por ofrecer soluciones prácticas de empaquetado
