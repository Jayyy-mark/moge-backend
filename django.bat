function django {
    param($cmd)

    switch ($cmd) {
        "start" {
            python manage.py runserver_plus --cert-file 192.168.20.39.pem --key-file 192.168.20.39-key.pem 192.168.20.39:8000
        }
        default {
            Write-Host "Unknown command"
        }
    }
}