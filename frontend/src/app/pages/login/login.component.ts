import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { IonicModule } from '@ionic/angular';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, IonicModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  username = '';
  password = '';

  constructor(private http: HttpClient, private router: Router) {}

  login() {
    const payload = {
      username: this.username,
      password: this.password
    };

    this.http.post<any>('http://localhost:8000/api/token/', payload).subscribe({
      next: res => {
        localStorage.setItem('access_token', res.access);
        localStorage.setItem('refresh_token', res.refresh);
        this.router.navigate(['/dashboard']); // o donde quieras ir luego
      },
      error: err => {
        alert('Credenciales incorrectas');
      }
    });
  }
}
