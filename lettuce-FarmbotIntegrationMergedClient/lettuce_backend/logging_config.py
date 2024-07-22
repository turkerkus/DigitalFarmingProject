import logging
import logging.config


def setup_logging():
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'app.log',
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True
            },
            'my_module': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False
            },
        }
    }
    logging.config.dictConfig(logging_config)
