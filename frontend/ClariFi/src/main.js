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
		defaultTheme: 'light',
		themes: {
			light: {
				colors: {
					primary: '#1976D2',
					secondary: '#424242',
					accent: '#82B1FF',
					error: '#FF5252',
					info: '#2196F3',
					success: '#4CAF50',
					warning: '#FFC107'
				}
			}
		}
	}
})

createApp(App)
	.use(vuetify)
	.mount('#app')
