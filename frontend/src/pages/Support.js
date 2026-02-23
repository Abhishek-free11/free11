import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  MessageCircle, Send, Bot, User, Ticket, Clock, 
  CheckCircle, AlertCircle, HelpCircle, Package
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Support = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Tickets state
  const [tickets, setTickets] = useState([]);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [createTicketOpen, setCreateTicketOpen] = useState(false);
  const [newTicket, setNewTicket] = useState({
    subject: '',
    description: '',
    category: 'other'
  });
  
  // Vouchers state
  const [vouchers, setVouchers] = useState([]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchInitialData = async () => {
    try {
      // Get chat suggestions
      const suggestionsRes = await api.getChatSuggestions();
      setSuggestions(suggestionsRes.data.suggestions || []);
      
      // Add greeting
      setMessages([{
        sender: 'bot',
        message: suggestionsRes.data.greeting || "Hi! How can I help you today?",
        timestamp: new Date().toISOString()
      }]);
      
      // Get tickets
      fetchTickets();
      
      // Get vouchers
      fetchVouchers();
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  };

  const fetchTickets = async () => {
    setTicketsLoading(true);
    try {
      const res = await api.getMyTickets();
      setTickets(res.data.tickets || []);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setTicketsLoading(false);
    }
  };

  const fetchVouchers = async () => {
    try {
      const res = await api.getMyVouchers();
      setVouchers(res.data.vouchers || []);
    } catch (error) {
      console.error('Error fetching vouchers:', error);
    }
  };

  const sendMessage = async (message) => {
    if (!message.trim()) return;
    
    // Add user message
    setMessages(prev => [...prev, {
      sender: 'user',
      message: message,
      timestamp: new Date().toISOString()
    }]);
    setInputMessage('');
    setChatLoading(true);
    
    try {
      const res = await api.sendChatMessage(message);
      const response = res.data;
      
      // Add bot response
      setMessages(prev => [...prev, {
        sender: 'bot',
        message: response.response,
        timestamp: new Date().toISOString(),
        action: response.action,
        data: response.data
      }]);
      
      // Update suggestions
      if (response.suggestions?.length > 0) {
        setSuggestions(response.suggestions);
      }
      
      // Handle actions
      if (response.action === 'create_ticket') {
        setCreateTicketOpen(true);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        sender: 'bot',
        message: "Sorry, I'm having trouble connecting. Please try again.",
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleCreateTicket = async () => {
    if (!newTicket.subject || !newTicket.description) {
      toast.error('Please fill all fields');
      return;
    }
    
    try {
      const res = await api.createTicket(newTicket);
      toast.success(`Ticket created! ID: ${res.data.ticket_id.slice(0, 8)}...`);
      setCreateTicketOpen(false);
      setNewTicket({ subject: '', description: '', category: 'other' });
      fetchTickets();
      
      // Add confirmation to chat
      setMessages(prev => [...prev, {
        sender: 'bot',
        message: `I've created support ticket #${res.data.ticket_id.slice(0, 8)}. Our team will respond within 24-48 hours. Is there anything else I can help with?`,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      toast.error('Failed to create ticket');
    }
  };

  const getStatusBadge = (status) => {
    const configs = {
      open: { color: 'bg-blue-500/20 text-blue-400', icon: AlertCircle },
      in_progress: { color: 'bg-yellow-500/20 text-yellow-400', icon: Clock },
      waiting_user: { color: 'bg-purple-500/20 text-purple-400', icon: HelpCircle },
      resolved: { color: 'bg-green-500/20 text-green-400', icon: CheckCircle },
      closed: { color: 'bg-slate-500/20 text-slate-400', icon: CheckCircle }
    };
    const config = configs[status] || configs.open;
    const Icon = config.icon;
    
    return (
      <Badge className={config.color}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getVoucherStatusBadge = (status) => {
    const configs = {
      pending: { color: 'bg-yellow-500/20 text-yellow-400' },
      processing: { color: 'bg-blue-500/20 text-blue-400' },
      delivered: { color: 'bg-green-500/20 text-green-400' },
      failed: { color: 'bg-red-500/20 text-red-400' }
    };
    return <Badge className={configs[status]?.color || configs.pending.color}>{status}</Badge>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-4 py-8" data-testid="support-page">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2 flex items-center gap-3">
            <MessageCircle className="h-10 w-10 text-green-400" />
            Help & Support
          </h1>
          <p className="text-slate-400">Chat with us or create a support ticket</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-slate-800/50 border border-slate-700">
            <TabsTrigger value="chat" className="data-[state=active]:bg-green-500">
              <Bot className="h-4 w-4 mr-2" />
              Chat Support
            </TabsTrigger>
            <TabsTrigger value="tickets" className="data-[state=active]:bg-blue-500">
              <Ticket className="h-4 w-4 mr-2" />
              My Tickets
            </TabsTrigger>
            <TabsTrigger value="vouchers" className="data-[state=active]:bg-purple-500">
              <Package className="h-4 w-4 mr-2" />
              My Vouchers
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Chat Window */}
              <Card className="lg:col-span-2 bg-slate-900/50 border-slate-800 h-[600px] flex flex-col">
                <CardHeader className="border-b border-slate-800">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Bot className="h-5 w-5 text-green-400" />
                    FREE11 Support Bot
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Ask about orders, coins, or get help
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col p-0">
                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="chat-messages">
                    {messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] p-3 rounded-lg ${
                            msg.sender === 'user'
                              ? 'bg-green-500/20 text-green-100'
                              : 'bg-slate-800 text-slate-200'
                          }`}
                        >
                          <div className="flex items-start gap-2">
                            {msg.sender === 'bot' && <Bot className="h-4 w-4 mt-1 text-green-400 flex-shrink-0" />}
                            <div className="whitespace-pre-wrap">{msg.message}</div>
                            {msg.sender === 'user' && <User className="h-4 w-4 mt-1 text-green-400 flex-shrink-0" />}
                          </div>
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-slate-800 p-3 rounded-lg">
                          <div className="flex items-center gap-2">
                            <Bot className="h-4 w-4 text-green-400" />
                            <div className="flex gap-1">
                              <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" />
                              <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                              <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                  
                  {/* Input */}
                  <div className="p-4 border-t border-slate-800">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Type your message..."
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendMessage(inputMessage)}
                        className="bg-slate-800 border-slate-700 text-white"
                        data-testid="chat-input"
                      />
                      <Button 
                        onClick={() => sendMessage(inputMessage)}
                        className="bg-green-500 hover:bg-green-600"
                        disabled={chatLoading}
                        data-testid="chat-send-btn"
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Suggestions */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Quick Help</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {suggestions.map((suggestion, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      className="w-full justify-start text-left border-slate-700 text-slate-300 hover:bg-slate-800"
                      onClick={() => sendMessage(suggestion)}
                      data-testid={`suggestion-${idx}`}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Tickets Tab */}
          <TabsContent value="tickets">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white">My Support Tickets</CardTitle>
                  <CardDescription className="text-slate-400">
                    Track your support requests
                  </CardDescription>
                </div>
                <Button 
                  onClick={() => setCreateTicketOpen(true)}
                  className="bg-blue-500 hover:bg-blue-600"
                  data-testid="create-ticket-btn"
                >
                  <Ticket className="h-4 w-4 mr-2" />
                  New Ticket
                </Button>
              </CardHeader>
              <CardContent>
                {ticketsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin h-8 w-8 border-4 border-blue-400 border-t-transparent rounded-full mx-auto" />
                  </div>
                ) : tickets.length === 0 ? (
                  <div className="text-center py-12">
                    <Ticket className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                    <p className="text-slate-400">No support tickets yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tickets.map((ticket) => (
                      <div 
                        key={ticket.id}
                        className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
                        data-testid={`ticket-${ticket.id}`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-white font-medium">{ticket.subject}</p>
                            <p className="text-sm text-slate-400 mt-1">
                              #{ticket.id.slice(0, 8)} • {ticket.category}
                            </p>
                          </div>
                          {getStatusBadge(ticket.status)}
                        </div>
                        <p className="text-slate-400 text-sm mt-2 line-clamp-2">
                          {ticket.description}
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                          Created: {new Date(ticket.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Vouchers Tab */}
          <TabsContent value="vouchers">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">My Vouchers</CardTitle>
                <CardDescription className="text-slate-400">
                  Track your redeemed vouchers and their status
                </CardDescription>
              </CardHeader>
              <CardContent>
                {vouchers.length === 0 ? (
                  <div className="text-center py-12">
                    <Package className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                    <p className="text-slate-400">No vouchers yet. Redeem your coins for rewards!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {vouchers.map((voucher) => (
                      <div 
                        key={voucher.id}
                        className="p-4 bg-slate-800/50 rounded-lg"
                        data-testid={`voucher-${voucher.id}`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-white font-medium">{voucher.product_name}</p>
                            <p className="text-sm text-slate-400">
                              Order: #{voucher.order_id?.slice(0, 8)}
                            </p>
                          </div>
                          {getVoucherStatusBadge(voucher.status)}
                        </div>
                        {voucher.status === 'delivered' && voucher.voucher_code && (
                          <div className="mt-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                            <p className="text-sm text-slate-400">Voucher Code:</p>
                            <p className="text-green-400 font-mono text-lg">{voucher.voucher_code}</p>
                            {voucher.voucher_pin && (
                              <p className="text-slate-400 text-sm mt-1">PIN: {voucher.voucher_pin}</p>
                            )}
                          </div>
                        )}
                        <p className="text-xs text-slate-500 mt-2">
                          {voucher.delivered_at 
                            ? `Delivered: ${new Date(voucher.delivered_at).toLocaleDateString()}`
                            : `Created: ${new Date(voucher.created_at).toLocaleDateString()}`
                          }
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Create Ticket Dialog */}
      <Dialog open={createTicketOpen} onOpenChange={setCreateTicketOpen}>
        <DialogContent className="bg-slate-900 border-slate-800">
          <DialogHeader>
            <DialogTitle className="text-white">Create Support Ticket</DialogTitle>
            <DialogDescription className="text-slate-400">
              Describe your issue and we'll get back to you within 24-48 hours.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-200">Subject</label>
              <Input
                placeholder="Brief description of your issue"
                value={newTicket.subject}
                onChange={(e) => setNewTicket({...newTicket, subject: e.target.value})}
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="ticket-subject-input"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm text-slate-200">Category</label>
              <select
                value={newTicket.category}
                onChange={(e) => setNewTicket({...newTicket, category: e.target.value})}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-md p-2"
                data-testid="ticket-category-select"
              >
                <option value="order">Order Issue</option>
                <option value="redemption">Redemption Problem</option>
                <option value="account">Account Issue</option>
                <option value="technical">Technical Problem</option>
                <option value="feedback">Feedback</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm text-slate-200">Description</label>
              <Textarea
                placeholder="Please describe your issue in detail..."
                value={newTicket.description}
                onChange={(e) => setNewTicket({...newTicket, description: e.target.value})}
                className="bg-slate-800 border-slate-700 text-white min-h-[120px]"
                data-testid="ticket-description-input"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateTicketOpen(false)} className="border-slate-700">
              Cancel
            </Button>
            <Button onClick={handleCreateTicket} className="bg-blue-500 hover:bg-blue-600" data-testid="submit-ticket-btn">
              Create Ticket
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Support;
