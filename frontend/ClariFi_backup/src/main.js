import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// Vuetify imports
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Material Design Icons
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
	components,
	directives,
	theme: {
		defaultTheme: 'dark',
		themes: {
			dark: {
				colors: {
					primary: '#00E5FF',   // Cyan Accent
					secondary: '#FFD740', // Gold Accent
					background: '#0F172A', // Deep Blue/Black
					surface: '#1E293B',    // Slightly lighter blue/black
					error: '#FF5252',
					info: '#2196F3',
					success: '#00E676',
					warning: '#FFC107'
				}
			}
		}
	}
})

createApp(App)
	.use(vuetify)
	.mount('#app')
