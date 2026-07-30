function django {
    param($cmd)

    switch ($cmd) {
        "start" {
            python manage.py runserver_plus 0.0.0.0:8000
        }
        default {
            Write-Host "Unknown command"
        }
    }
}